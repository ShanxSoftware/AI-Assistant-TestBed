# demos/demo_disc_personalities.py  (runnable script)
for arch in [Archetype.DRIVER, ...]:
    h = XAI_Handler(...)
    h.set_personality(...)  # different per loop
    print(h.chat("Plan a team meeting", session_id=f"demo-{arch}"))