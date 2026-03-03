# conftest.py  (top-level)
import os
import dotenv 
import pytest
from xaihandler import (
    xAI_Handler,
    AgentPersonality, 
    Archetype, 
    ToolDefinition,
    ToolRegistry, 
    BudgetExceeded,
    AgentTrait, 
    Trait
)

@pytest.fixture(scope="session")
def api_key():
    key = os.getenv("XAI_API_KEY")
    if not key:
        pytest.skip("XAI_API_KEY not set")
    return key

@pytest.fixture(scope="session")
def api_model(): 
    model = os.getenv("XAI_MODEL")
    if not model: 
        pytest.skip("XAI_MODEL not set")
    return model

@pytest.fixture(scope="session")
def api_timeout(): 
    timeout = os.getenv("XAI_TIMEOUT")
    if not timeout: 
        pytest.skip("XAI_TIMEOUT not set")
    return timeout

@pytest.fixture(params=list(Archetype))
def agent(request):
    p=AgentPersonality(
        name=f"Buster - {request.param.value.title()} - Test Bot",
        gender="male",
        primary_archetype=request.param,
        primary_weight=1.0,
        job_description="Assist in Unit Testing xAI-SDK/API functions",
        traits=[] # minimal; extend per archetype in specific tests
    )
    assert len(p.traits) <= 5  # explicit trait cap check
    return p

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
    h = xAI_Handler(api_key=api_key, 
                    model=api_model, 
                    timeout=api_timeout, 
                    validate_connection=False)
    h.set_personality(p)
    # register one shared tool for all tests
    from pydantic import BaseModel
    class EchoInput(BaseModel):
        text: str
    def echo_tool(text: str):
        return f"Echo: {text}"
    h.add_tool(ToolDefinition("echo", "Echo text", echo_tool, EchoInput))
    yield h
    # cleanup: optional delete temp db if needed