# tests/test_memory_persistence.py
def test_full_state_save_load(assistant):
    sess = "persist-1"
    assistant.chat("Secret code is 4242", session_id=sess)
    assistant.save_state("test-assist-1")
    fresh = xAI_Handler(api_key=assistant.client.api_key)  # new instance
    fresh.load_state("test-assist-1")
    resp = fresh.chat("What is the secret code?", session_id=sess)
    assert "4242" in resp["content"]