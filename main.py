import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from agents.debater import DebaterAgent, DebateMessage

app = FastAPI(title="Climate Debate Simulator")

# Serve the main interface
@app.get("/")
async def read_index():
    return FileResponse("static/index.html")

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/policies/{country_code}")
async def get_policy(country_code: str):
    country_code = country_code.lower()
    if country_code not in ["usa", "eu", "china"]:
        raise HTTPException(status_code=404, detail="Country policy not found")
        
    filepath = f"data/policies/{country_code}_policy.json"
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Policy file missing")
        
    with open(filepath, "r") as f:
        data = json.load(f)
    return data

class DebateRequest(BaseModel):
    topic: str
    rounds: int = Field(ge=1, le=5)

class DebateResponse(BaseModel):
    messages: list[DebateMessage]

@app.post("/debate/start", response_model=DebateResponse)
async def start_debate(request: DebateRequest):
    agents = [
        DebaterAgent("USA"),
        DebaterAgent("EU"),
        DebaterAgent("China")
    ]
    
    history: list[DebateMessage] = []
    
    for round_num in range(1, request.rounds + 1):
        for agent in agents:
            try:
                msg = await agent.generate_response(request.topic, round_num, history)
                history.append(msg)
            except Exception as e:
                from datetime import datetime, timezone
                fallback_msg = DebateMessage(
                    round=round_num,
                    agent=agent.country,
                    message=f"I experienced a technical failure: {str(e)}",
                    stance="neutral",
                    timestamp=datetime.now(timezone.utc).isoformat()
                )
                history.append(fallback_msg)
                
    return DebateResponse(messages=history)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
