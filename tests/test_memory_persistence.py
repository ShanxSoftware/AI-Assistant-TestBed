# tests/test_memory_persistence.py
import re
from xaihandler import (
    xAI_Handler,
    MemoryStore
)
def test_full_state_save_load(assistant):
    # Setup Chat Session
    response = assistant.chat(message="Hello what is your name?")
    assert "Test" in response["content"] and "Bot" in response["content"]
    # Continue Session
    response2 = assistant.chat(message="It's nice to meet you.", previous_response_id=response["response_id"])
    assert response2["content"] is not None 
    # Test Client Tool
    response3 = assistant.chat(message="Use the EchoInput tool on the following input: Client Tool successful", previous_response_id=response2["response_id"])
    print(response3["content"])
    assert any(word in response3["content"].lower() for word in ["perfect", "client tool successful", "mission accomplished", "tool executed successfully", "tool echo confirmed"]), "API response not in the expected list of responses for echo_tool"
    # Check session ID is consistant
    assert assistant.memory.get_session_id_from_response_id(response_id=response["response_id"]) == assistant.memory.get_session_id_from_response_id(response_id=response2["response_id"]) and assistant.memory.get_session_id_from_response_id(response_id=response["response_id"]) == assistant.memory.get_session_id_from_response_id(response_id=response3["response_id"])
    # Check global context store and retrieval
    response4 = assistant.chat(message="I need you to remember this secret code 4374", previous_response_id=response3["response_id"])
    print(response4["content"])
    print(assistant.memory.list_global_keys())
    response5 = assistant.chat(message="Did you store the code in the global_context?")
    print(response5["content"])
    content_lower = response5["content"].lower()
    store_signals = ["yes", "yeah", "stored", "saved", "locked", "confirmed", "vault", "memory", "context", "key"]
    assert any(s in content_lower for s in store_signals), f"No storage confirmation signal found:\n{response5['content']}"
    
    print("new chat")
    newChat1 = assistant.chat(message="TestBot, do you remember the secret code?")
    print(newChat1["content"])
    if "4374" not in newChat1["content"]:
        newChat1_5 = assistant.chat(message="Did you search the global_context", previous_response_id=newChat1["response_id"])
        print(newChat1_5["content"])
    newchat2 = assistant.chat(message="The new secret code is 7349, don't forget.", previous_response_id=newChat1_5["response_id"] if newChat1_5 else newChat1["response_id"])
    print(newchat2["content"])
    print(assistant.memory.list_global_keys())
    assert "7349" in newchat2["content"]
    newchat3 = assistant.chat(message="Did you store the code imn the global_context?", previous_response_id=newchat2["response_id"])
    print(newchat3["content"])
    # The previous prompt hopefully overwrites the previous code, let's check.
    thirdChat = assistant.chat(message="What secrets do you know?")
    probe_response = assistant.chat(
        message="What is the current secret code? Reply with **only** the 4-digit number, nothing else.",
        previous_response_id=thirdChat["response_id"]
    )

    probe_text = probe_response["content"].strip()

    # Extract first 4-digit number (ignores bold, spaces, markdown, extra text)
    digits = ''.join(c for c in probe_text if c.isdigit())
    if len(digits) >= 4:
        first_four = digits[:4]
        assert first_four == "7349", \
            f"Probe expected 7349, extracted '{first_four}' from:\n{probe_text}\nFull reply:\n{thirdChat['content']}"
    else:
        assert False, f"No 4-digit code found in probe:\n{probe_text}\nFull reply:\n{thirdChat['content']}"

    assert "4374" not in probe_text, "Old code in probe response"
        