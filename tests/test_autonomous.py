# tests/test_autonomous.py

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from xaihandler import xAI_Handler
from xaihandler.personality import AgentPersonality, Archetype
from xaihandler.memorystore import MemoryStore
from xaihandler.definitions import AutonomousOutput, JOB_STATUS, JobCard, BatchStatus

@pytest.fixture(scope="function")
def fresh_handler(tmp_path):
    """Isolated handler + in-memory DB — avoids conftest.py side-effects."""
    db_path = tmp_path / "test_autonomous.db"
    h = xAI_Handler(token_budget=1_000_000)
    h.memory = MemoryStore(db_path=str(db_path))  # overrides default
    # Minimal personality — no real API calls
    h.personality = AgentPersonality(
        name="Buster",
        gender="male",
        primary_archetype=Archetype.DRIVER,
        primary_weight=1.0,
        job_description="You are part of the unit test, helping verify code function"
    )
    h._execute = True     # allow loop to run
    yield h
    h.set_execute(False)  # cleanup

@pytest.fixture
def mock_client(fresh_handler):
    """Replace real client with mocks — only for this test file."""
    with patch.object(fresh_handler, 'client') as mock_client:
        mock_client.batch.create.return_value = MagicMock(batch_id="mock-batch-123")
        mock_client.batch.add.return_value = None
        mock_client.batch.get.return_value = MagicMock(state=MagicMock(num_pending=0, num_success=1, num_error=0))
        mock_client.batch.list_batch_results.return_value = MagicMock(
            succeeded=[MagicMock(
                batch_request_id="mock-job-1",
                response=MagicMock(
                    content='{"action":"continue","next_task":"step2","status":"in progress","progress":0.5,"user_message":"","reasoning_summary":"thought","result":"did step1","clarification_needed":false,"job_card":{"job_title":"Test"}}',
                    tool_calls=[],
                    role="assistant",
                    usage=MagicMock(total_tokens=400, prompt_tokens=200, completion_tokens=200)
                )
            )],
            failed=[],
            pagination_token=None
        )
        yield mock_client

@pytest.fixture(autouse=True)
def enforce_mock_client(monkeypatch, fresh_handler):
    """Force mock on the instance — survives conftest.py overrides."""
    mock = MagicMock()
    mock.batch.create.return_value = MagicMock(batch_id="mock-batch-123")
    mock.batch.add.return_value = None
    mock.batch.get.return_value = MagicMock(state=MagicMock(num_pending=0, num_success=1, num_error=0))
    
    # This is the critical line for your failing test
    bad_result = MagicMock()
    bad_result.batch_request_id = "mock-job-1"
    bad_result.response = MagicMock()
    bad_result.response.content = '{"broken"}'          # deliberately invalid
    bad_result.response.tool_calls = []
    bad_result.response.role = "assistant"
    bad_result.response.usage = MagicMock(total_tokens=100)
    
    mock.batch.list_batch_results.return_value = MagicMock(
        succeeded=[bad_result],
        failed=[],
        pagination_token=None
    )
    
    monkeypatch.setattr(fresh_handler, 'client', mock)
    yield mock

def test_loop_exits_on_empty_queue(fresh_handler):
    fresh_handler.execution_loop(test_mode=True)  # runs once, sees no jobs
    assert fresh_handler.get_execute() is False

def test_sleep_calculates_correct_delta(fresh_handler, enforce_mock_client):
    # Simulate previous batch
    fresh_handler.memory.upsert_batch(BatchStatus(
        batch_id="prev",
        session_id="sess",
        batch_send=datetime.now() - timedelta(seconds=12),
        incomplete=False
    ))
    start = datetime.now()
    # Run loop once — should sleep ~18 s
    fresh_handler.execution_loop(test_mode=True)
    elapsed = (datetime.now() - start).total_seconds()
    assert 5 < elapsed < 22

def test_handles_parse_failure(fresh_handler, enforce_mock_client):
    # Build the bad result explicitly
    bad_result = MagicMock()
    bad_result.batch_request_id = "mock-job-1"
    bad_result.response = MagicMock()
    bad_result.response.content = '{"broken"}'  # invalid JSON
    bad_result.response.tool_calls = []
    bad_result.response.role = "assistant"
    bad_result.response.usage = MagicMock(total_tokens=100, prompt_tokens=50, completion_tokens=50)

    # Set the mock return value
    enforce_mock_client.batch.list_batch_results.return_value = MagicMock(
        succeeded=[bad_result],
        failed=[],
        pagination_token=None
    )
    # Override mock to return bad JSON
    # enforce_mock_client.batch.list_batch_results.return_value.succeeded[0].response.content = '{"broken"}'
    # Add one job first
    fresh_handler.memory.add_job(title="ParseFailTest", job_card=JobCard(job_title="ParseFailTest"))
    fresh_handler.execution_loop(test_mode=True)  # runs batch, hits parse error
    assert isinstance(fresh_handler.client, MagicMock), "Real client was used instead of mock"
    jobs = fresh_handler.memory.get_jobs()
    assert len(jobs) == 1
    assert jobs[0].status == JOB_STATUS.BLOCKED   # status index — adjust to your get_jobs return tuple
    assert jobs[0].clarification_needed             # clarification_needed