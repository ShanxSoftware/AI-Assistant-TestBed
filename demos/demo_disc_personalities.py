# demos/demo_disc_personalities.py
if __name__ == "__main__":
    from xai_ai_library.handler import xAI_Handler
    from xai_ai_library.personality import AgentPersonality, Archetype
    import os
    h = xAI_Handler(os.getenv("XAI_API_KEY"))
    for arch in Archetype:
        p = AgentPersonality(...)  # fill per arch as in fixture
        h.set_personality(p)
        print(f"\n=== {arch.value.upper()} ===")
        print(h.chat("Greet a new user and suggest one action", session_id=f"demo-{arch}"))