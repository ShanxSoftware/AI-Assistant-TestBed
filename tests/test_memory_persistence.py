# tests/test_memory_persistence.py
def test_session_save_load(assistant):
    sess = "persist-test"
    assistant.chat("Remember this number: 42", session_id=sess)
    assistant.save_state("test-assistant-1")
    new_h = XAI_Handler(...)  # fresh instance
    new_h.load_state("test-assistant-1")
    resp = new_h.chat("What number did I tell you?", session_id=sess)
    assert "42" in resp["content"]