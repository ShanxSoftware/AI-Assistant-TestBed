# tests/test_user_interaction.py
def test_conversational_chat(assistant):
    sess = "test-conv-1"
    resp1 = assistant.chat("Hello, my name is Jakob", session_id=sess)
    resp2 = assistant.chat("What is my name?", session_id=sess)  # must remember via memory
    assert "Jakob" in resp2["content"]
    # assert memory persisted
    ctx = assistant.memory.get_context(sess)
    assert any("Jakob" in m["content"] for m in ctx)

def test_tool_loop_and_cache(assistant):
    # register a dummy tool that returns fixed result
    ...
    resp = assistant.chat("What is the weather in Sydney?", session_id="tool-test")
    # second identical call must hit cache (check via usage log or internal counter)
    ...