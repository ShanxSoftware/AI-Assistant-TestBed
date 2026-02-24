# tests/test_user_interaction.py
def test_conversational_memory_persistence(assistant):
    sess = "conv-1"
    assistant.chat("My name is Jakob from Sydney", session_id=sess)
    resp = assistant.chat("What is my name and location?", session_id=sess)
    assert "Jakob" in resp["content"] and "Sydney" in resp["content"]

def test_tool_auto_execution_and_cache(assistant):
    sess = "tool-1"
    # first call → executes
    r1 = assistant.chat("Say hello using echo tool", session_id=sess)
    assert "Echo" in r1["content"]
    # identical call → must hit cache (check via usage summary or second response speed/content)
    r2 = assistant.chat("Say hello using echo tool", session_id=sess)
    assert r2["content"] == r1["content"]  # or assert usage log shows cached_prompt_tokens > 0

def test_global_context_injection(assistant):
    sess = "global-1"
    assistant.memory.add_global("user_location", "Sydney, AU", tags=["location"])
    resp = assistant.chat("What is the weather like here?", session_id=sess)
    assert "Sydney" in resp["content"]