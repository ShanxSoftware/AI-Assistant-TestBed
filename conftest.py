# conftest.py  (top-level)
import os
import dotenv 
import pytest
from xaihandler import (
    xAI_Handler,
    AgentPersonality, 
    Archetype, 
    AgentTrait, 
    Trait,
    StatefulMemory
)

@pytest.fixture(scope="session")
def api_key():
    key = os.getenv("XAI_API_KEY")
    if not key:
        pytest.skip("XAI_API_KEY not set")
    return key

@pytest.fixture(params=list(Archetype))
def assistant(request, api_key, tmp_path):
    p = AgentPersonality(
        name=f"Test{request.param.value.title()}Bot",
        gender="unspecified",
        primary_archetype=request.param,
        primary_weight=1.0,
        job_description="helpful test assistant",
        traits=[]  # minimal; extend per archetype in specific tests
    )
    h = xAI_Handler(api_key=api_key)
    h.set_personality(p)
    # register one shared tool for all tests
    from pydantic import BaseModel
    class EchoInput(BaseModel):
        text: str
    def echo_tool(text: str):
        return f"Echo: {text}"
    h.add_tool("echo", echo_tool, EchoInput, "Simple echo for testing")
    yield h
    # cleanup: optional delete temp db if needed