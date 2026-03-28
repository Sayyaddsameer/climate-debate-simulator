import os
import httpx
from pydantic import BaseModel
from datetime import datetime, timezone
import re
from core.rag_service import rag_service

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "llama3:8b")

class DebateMessage(BaseModel):
    round: int
    agent: str
    message: str
    stance: str
    timestamp: str

class DebaterAgent:
    def __init__(self, country: str):
        self.country = country

    async def generate_response(self, topic: str, current_round: int, history: list[DebateMessage]) -> DebateMessage:
        # Format history string
        history_text = "\n".join([f"Round {msg.round} - {msg.agent}: {msg.message}" for msg in history])
        if not history_text:
            history_text = "No history yet. This is the opening statement."

        # RAG Query
        query = f"Topic: {topic}. Recent points: {history_text[-500:]}"
        policy_context = rag_service.get_context(query, self.country)

        prompt = f"""You are the debate representative for {self.country}.
You are debating the topic: {topic}.
Here is the debate history so far:
{history_text}

Your response must be based on your country's official policy points:
{policy_context}

Your response must be a single paragraph. Conclude your response by stating your stance as 'supportive', 'opposed', or 'neutral'.
"""

        url = f"{OLLAMA_BASE_URL}/api/generate"
        payload = {
            "model": LLM_MODEL_NAME,
            "prompt": prompt,
            "stream": False
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=60.0)
                response.raise_for_status()
                data = response.json()
                raw_message = data.get("response", "").strip()
        except Exception as e:
            raw_message = f"I am unable to provide a response at this time. I am neutral."

        # Extract stance
        stance = "neutral"
        lower_msg = raw_message.lower()
        if "supportive" in lower_msg:
            stance = "supportive"
        elif "opposed" in lower_msg:
            stance = "opposed"
        elif "neutral" in lower_msg:
            stance = "neutral"

        timestamp = datetime.now(timezone.utc).isoformat()

        return DebateMessage(
            round=current_round,
            agent=self.country,
            message=raw_message,
            stance=stance,
            timestamp=timestamp
        )
