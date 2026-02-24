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

@pytest.fixture(params=[Archetype.DRIVER, Archetype.EXPRESSIVE, Archetype.AMIABLE, Archetype.ANALYTICAL])
def assistant(request, tmp_path):
    p = AgentPersonality(
        name=f"Test{request.param.value.title()}",
        gender="unspecified",
        primary_archetype=request.param,
        primary_weight=1.0,
        job_description="test assistant",
        traits=[]  # or minimal set for each archetype
    )
    
    h = xAI_Handler(api_key="...")  # or from env fixture
    h.set_personality(p)
    # register any shared tools once
    h.register_tool(...)  
    yield h
    # optional cleanup