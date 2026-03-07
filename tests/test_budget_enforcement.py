# tests/test_budget_enforcement.py
import datetime
import pytest
import sqlite3
from unittest.mock import patch, MagicMock
from xaihandler import xAI_Handler, BudgetExceeded, DailySoftBudgetExceeded
from xaihandler.memorystore import MemoryStore
from xaihandler.personality import AgentPersonality, Archetype
from xaihandler.definitions import CONTEXT_MODE

def insert_fake_usage(memory: MemoryStore, days_ago: int, total_tokens: int):
    past_date = datetime.date.today() - datetime.timedelta(days=days_ago)
    fake_timestamp = past_date.isoformat() + "T12:00:00"
    
    session_id = memory.start_session(f"fake-{days_ago}")
    memory.add_message(
        session_id=session_id,
        role="assistant",
        content="fake",
        display=True,
        response_id=f"fake-{days_ago}",
        total_tokens=total_tokens,
        prompt_tokens=total_tokens // 3,
        completion_tokens=total_tokens // 3 * 2,
        reasoning_tokens=0,
        cached_prompt_tokens=0,
        server_side_tools_used=0
    )

# ────────────────────────────────────────────────
# Single clean autouse fixture — mocks only network parts
# ────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def mock_xai_client_creation():
    """Replace real Client with a fully mocked version for all tests."""
    with patch("xai_sdk.Client") as MockClient:
        mock_client = MockClient.return_value   # this is what self.client becomes

        # Mock tokenizer (used in _precall_check)
        mock_tokenizer = MagicMock()
        mock_tokenizer.tokenize_text.return_value = [1] * 12  # fake ~12 tokens
        mock_client.tokenize = mock_tokenizer

        # Mock chat lifecycle
        mock_chat_factory = MagicMock()
        mock_client.chat = mock_chat_factory

        mock_chat = MagicMock()
        mock_chat.append = MagicMock()

        mock_response = MagicMock(
            role="assistant",
            content="Mock safe response",
            id="mock-id-123",
            tool_calls=[],
            usage=MagicMock(
                prompt_tokens=20,
                completion_tokens=40,
                total_tokens=60,
                reasoning_tokens=0,
                cached_prompt_tokens=0,
                server_side_tools_used=0
            )
        )
        mock_chat.sample.return_value = mock_response
        mock_chat_factory.create.return_value = mock_chat

        yield

# ────────────────────────────────────────────────
# Handler fixture — higher budget, no broken monkeypatch
# ────────────────────────────────────────────────

@pytest.fixture
def budget_test_handler(api_key, tmp_path):
    db_path = tmp_path / "budget_test.db"
    h = xAI_Handler(
        api_key=api_key or "fake-key-unit-test",
        model="grok-beta",
        timeout=30,
        token_budget=10_000,           # high enough to reach daily logic
        max_client_tool_calls=2
    )
    h.memory = MemoryStore(db_path=str(db_path))
    h.set_personality(
        AgentPersonality(
            name="BudgetTestBot",
            gender="unspecified",
            primary_archetype=Archetype.ANALYTICAL,
            primary_weight=1.0,
            job_description="test assistant"
        )
    )
    # echo tool (optional)
    from pydantic import BaseModel
    class Echo(BaseModel):
        text: str
    h.add_tool("echo", "echo input", Echo, lambda t: f"Echo: {t}")
    
    return h


# TODO: Budget-guard tests currently rely on real API calls due to mocking challenges.
#       Revisit with proper instance-level mocking or injectable Client when time allows.
#       Current manual runs confirm enforcement works as intended.


# ────────────────────────────────────────────────
# Tests — adjusted expectations for fallback estimation
# ────────────────────────────────────────────────

def test_monthly_budget_hard_limit_reached(budget_test_handler):
    h = budget_test_handler
    insert_fake_usage(h.memory, days_ago=2, total_tokens=9800)

    response = h.chat("Test monthly exceed")

    assert "budget-rejected" in response.get("response_id", "")
    assert any(word in response["content"].lower() for word in ["budget", "exceeded", "limit"])
    assert response["usage"]["total_tokens"] == 0

    # Verify DB side-effect
    with sqlite3.connect(h.memory.db_path) as conn:
        row = conn.execute(
            "SELECT content, response_id, total_tokens FROM messages "
            "WHERE role = 'assistant' ORDER BY id DESC LIMIT 1"
        ).fetchone()
        assert row
        assert "exceeded" in row[0].lower() or "budget" in row[0].lower()
        assert row[1].startswith("budget-rejected")
        assert row[2] == 0

def test_daily_soft_cap_enforced_no_carryover(budget_test_handler):
    h = budget_test_handler
    insert_fake_usage(h.memory, days_ago=0, total_tokens=8000)

    response = h.chat(message="This should hit daily soft cap")

    assert "budget-rejected" in response["response_id"]
    assert "daily" in response["content"].lower() or "soft" in response["content"].lower()
    assert response["usage"]["total_tokens"] == 0
    # Verify DB side-effect
    with sqlite3.connect(h.memory.db_path) as conn:
        row = conn.execute(
            "SELECT content, response_id, total_tokens FROM messages "
            "WHERE role = 'assistant' ORDER BY id DESC LIMIT 1"
        ).fetchone()
        assert row
        assert "exceeded" in row[0].lower() or "budget" in row[0].lower()
        assert row[1].startswith("budget-rejected")
        assert row[2] == 0

def test_daily_carryover_allows_extra_usage(budget_test_handler):
    h = budget_test_handler
    insert_fake_usage(h.memory, days_ago=1, total_tokens=100)
    insert_fake_usage(h.memory, days_ago=0, total_tokens=2000)

    response = h.chat(message="Short message — should pass with carry-over")
    print(f"response content: {response["content"]}")
    assert "budget-rejected" not in response["response_id"]
    assert response["content"] == "Mock safe response"   # from mock
    assert response["usage"]["total_tokens"] == 60       # from mock usage

# zero-budget and under-limit tests unchanged — should work