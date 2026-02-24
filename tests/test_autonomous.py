# tests/test_autonomous.py
def test_run_autonomous_structured_loop(assistant):
    task = "Plan a 2-hour meeting in Sydney next week under $500 budget using tools if needed"
    result = assistant.run_autonomous(task, session_id="auto-1", max_steps=6)
    assert "final_answer" in result or "meeting" in result["content"].lower()
    # assert stopped correctly, budget not exceeded

def test_budget_guard_prevents_overrun(assistant):
    assistant.set_daily_budget(200)  # public guard setter
    with pytest.raises(Exception):  # or specific BudgetExceeded
        assistant.run_autonomous("Call echo tool 50 times", max_steps=50, session_id="budget-test")