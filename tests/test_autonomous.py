# tests/test_autonomous.py
def test_run_autonomous_budget_guard(assistant):
    assistant.budget.set_daily_limit(1000)  # expose only via public method
    with pytest.raises(BudgetExceeded):
        assistant.run_autonomous("Perform 20 expensive tool calls", max_steps=30)

def test_structured_reasoning_loop(assistant):
    task = "Book the cheapest flight Sydney to Melbourne under $300"
    result = assistant.run_autonomous(task, max_steps=8)
    assert "final_answer" in result  # or check content contains booking info