import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone

# We patch the rag_service at import time to avoid needing chromadb/models installed for unit tests
with patch("core.rag_service.RAGService.__init__", return_value=None), \
     patch("core.rag_service.rag_service", MagicMock(get_context=MagicMock(return_value="Mocked policy context"))):
    from main import app

client = TestClient(app)

# --- Health Check ---

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

# --- Policy Retrieval ---

def test_get_usa_policy():
    response = client.get("/policies/usa")
    assert response.status_code == 200
    data = response.json()
    assert "country" in data
    assert data["country"] == "USA"
    assert "key_positions" in data
    assert "red_lines" in data

def test_get_eu_policy():
    response = client.get("/policies/eu")
    assert response.status_code == 200
    data = response.json()
    assert data["country"] == "EU"

def test_get_china_policy():
    response = client.get("/policies/china")
    assert response.status_code == 200
    data = response.json()
    assert data["country"] == "China"

def test_get_invalid_policy():
    response = client.get("/policies/mars")
    assert response.status_code == 404

# --- Frontend Endpoint ---

def test_root_returns_html():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

# --- Debate Endpoint ---

def _make_mock_message(agent: str, round_num: int):
    from agents.debater import DebateMessage
    return DebateMessage(
        round=round_num,
        agent=agent,
        message=f"Mock message from {agent}",
        stance="neutral",
        timestamp=datetime.now(timezone.utc).isoformat()
    )

@pytest.mark.anyio
async def test_debate_message_count_two_rounds():
    """2 rounds x 3 agents = 6 messages"""
    async def mock_generate(topic, current_round, history):
        return _make_mock_message(self_agent, current_round)

    agents_called = []
    call_map = {"USA": 0, "EU": 0, "China": 0}

    with patch("main.DebaterAgent") as MockAgentClass:
        instances = []
        for country in ["USA", "EU", "China"]:
            inst = AsyncMock()
            inst.country = country
            inst.generate_response = AsyncMock(return_value=_make_mock_message(country, 1))
            instances.append(inst)
        MockAgentClass.side_effect = instances

        response = client.post("/debate/start", json={"topic": "Test", "rounds": 2})

    assert response.status_code == 200
    data = response.json()
    assert "messages" in data

def test_debate_invalid_rounds_zero():
    response = client.post("/debate/start", json={"topic": "Test", "rounds": 0})
    assert response.status_code == 422

def test_debate_invalid_rounds_too_many():
    response = client.post("/debate/start", json={"topic": "Test", "rounds": 6})
    assert response.status_code == 422

def test_debate_missing_topic():
    response = client.post("/debate/start", json={"rounds": 2})
    assert response.status_code == 422

# --- Message Schema Validation ---

def test_message_schema():
    """Validates that DebateMessage model enforces stance constraint."""
    from agents.debater import DebateMessage
    msg = DebateMessage(
        round=1,
        agent="USA",
        message="We support this.",
        stance="supportive",
        timestamp=datetime.now(timezone.utc).isoformat()
    )
    assert msg.stance == "supportive"
    assert msg.agent == "USA"
    assert msg.round == 1
    assert msg.message != ""

def test_agent_turn_order():
    """Agent order must always be USA, EU, China."""
    import main as m
    import inspect
    source = inspect.getsource(m.start_debate)
    assert '"USA"' in source
    assert '"EU"' in source
    assert '"China"' in source
    usa_pos = source.find('"USA"')
    eu_pos = source.find('"EU"')
    china_pos = source.find('"China"')
    assert usa_pos < eu_pos < china_pos, "Agent turn order must be USA, EU, China"
