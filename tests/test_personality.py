# tests/test_personality.py  (full replacement - original 5 tests unchanged)
import pytest
import logging
from pydantic import ValidationError   # <-- only new import
from xaihandler import (
    Archetype,
    Trait,
    AgentTrait,
    AgentPersonality,
)

"""
Tests for personality.py
- Validates fixture creation (DISC parametrization)
- Exercises core functions, validation, and prompt blending
Author: Jakob Shanks + Grok
Requires: pytest, xai-ai-library
"""

def test_agent_fixture(agent):
    assert agent is not None
    assert agent.gender == "male"
    assert "Buster" in agent.name
    assert "Unit Test" in agent.job_description
    assert "You are" in agent.system_prompt
    assert agent.to_json()  # non-empty
    assert len(agent.traits) <= 5  # explicit cap check


def test_personality():
    p = AgentPersonality(
        name="Adam",
        gender="male",
        primary_archetype=Archetype.DRIVER,
        primary_weight=1.0,
        job_description="Assist in Unit Testing xAI-SDK/API functions",
        traits=[AgentTrait(trait=Trait.PRECISION, intensity=50)]
    )
    assert p is not None
    assert p.gender == "male"
    assert "Adam" in p.name
    assert "Unit Test" in p.job_description
    assert "You are" in p.system_prompt
    assert p.to_json()  # non-empty


def test_disc_prompt_content_per_archetype(agent):
    """Verifies each archetype actually injects its characteristic language."""
    prompt = agent.system_prompt.lower()
    archetype = agent.primary_archetype
    if archetype == Archetype.DRIVER:
        assert any(word in prompt for word in ["direct", "decisive", "action-oriented"])
    elif archetype == Archetype.EXPRESSIVE:
        assert any(word in prompt for word in ["enthusiastic", "persuasive", "storytelling"])
    elif archetype == Archetype.AMIABLE:
        assert any(word in prompt for word in ["empathetic", "supportive", "warm"])
    elif archetype == Archetype.ANALYTICAL:
        assert any(word in prompt for word in ["precise", "logical", "detail-oriented"])


def test_weight_and_trait_validation():
    # valid blend
    p = AgentPersonality(
        name="BlendTest",
        gender="unspecified",
        primary_archetype=Archetype.DRIVER,
        primary_weight=0.6,
        secondary_archetype=Archetype.AMIABLE,
        job_description="test",
        traits=[AgentTrait(trait=Trait.CONFIDENCE, intensity=80)]
    )
    assert p.secondary_weight == 0.4
    assert p.primary_weight == 0.6

    # invalid cases - Pydantic field constraint fires first (correct behaviour)
    with pytest.raises(ValidationError, match="greater_than_equal"):
        AgentPersonality(
            name="BadWeight",
            gender="unspecified",
            primary_archetype=Archetype.DRIVER,
            primary_weight=0.4,          # < 0.5
            secondary_archetype=Archetype.AMIABLE,
            job_description="test"
        )

    with pytest.raises(ValidationError, match="Max 5 traits"):
        AgentPersonality(
            name="TooMany",
            gender="unspecified",
            primary_archetype=Archetype.DRIVER,
            primary_weight=1.0,
            job_description="test",
            traits=[AgentTrait(trait=Trait.WARMTH, intensity=100)] * 6
        )


def test_trait_synergy_warnings(caplog):
    """Checks that archetype synergy logger tips fire correctly."""
    with caplog.at_level(logging.WARNING):
        AgentPersonality(
            name="AmiableLowWarmth",
            gender="male",
            primary_archetype=Archetype.AMIABLE,
            primary_weight=1.0,          # <-- required when no secondary_archetype
            job_description="test",
            traits=[AgentTrait(trait=Trait.WARMTH, intensity=30)]
        )
    assert any("Boost 'warmth'" in message for message in caplog.messages)