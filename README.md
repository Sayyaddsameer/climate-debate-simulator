# Climate Policy Debate Simulator

A multi-agent AI application that simulates a structured policy debate between three geopolitical entities (the **USA**, the **EU**, and **China**) using **FastAPI**, **Ollama** (local LLMs), and **RAG** (Retrieval-Augmented Generation) via ChromaDB.

---

## Table of Contents

- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [API Reference](#api-reference)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Testing](#testing)

---

## Architecture

```
User (Browser)
     |
     v
FastAPI (main.py)
     |-- GET /health
     |-- GET /policies/{country_code}
     +-- POST /debate/start
              |
              v
     DebaterAgent (agents/debater.py)
              | RAG Query
              v
     RAGService (core/rag_service.py)
       ChromaDB + SentenceTransformers
              |
              v
     Ollama LLM (llama3:8b)
```

- **FastAPI** orchestrates multi-turn debates, maintaining history and agent turn order (USA -> EU -> China).
- **RAGService** ingests JSON policy documents at startup into **ChromaDB**, and retrieves relevant policy context per-country at each turn.
- **DebaterAgent** builds a structured prompt using the RAG context, debate history, and sends it to the local Ollama LLM.

---

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) installed
- At least **8 GB of RAM** available for the Ollama model

---

## Quick Start

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd climate-debate-simulator
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` if needed (defaults work for local Docker Compose):

```
OLLAMA_BASE_URL=http://ollama:11434
LLM_MODEL_NAME=llama3:8b
```

### 3. Start the application

```bash
docker-compose up -d --build
```

This will:
1. Pull and start the **Ollama** container.
2. Build and start the **FastAPI** application container.
3. The Ollama service will download the `llama3:8b` model on first run (may take a few minutes).

### 4. Pull the LLM model (first time only)

```bash
docker exec -it $(docker-compose ps -q ollama) ollama pull llama3:8b
```

### 5. Access the application

- **Frontend UI**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## API Reference

### `GET /health`

Returns the health status of the API.

**Response:**
```json
{ "status": "ok" }
```

---

### `GET /policies/{country_code}`

Returns the full policy document for a country.

**Path Params:** `country_code` - one of `usa`, `eu`, `china`

**Example:**
```bash
curl http://localhost:8000/policies/usa
```

**Response:**
```json
{
  "country": "USA",
  "key_positions": ["..."],
  "red_lines": ["..."]
}
```

---

### `POST /debate/start`

Starts the multi-agent debate simulation.

**Request Body:**
```json
{
  "topic": "Implementing a global carbon tax",
  "rounds": 2
}
```

**Response:**
```json
{
  "messages": [
    {
      "round": 1,
      "agent": "USA",
      "message": "...",
      "stance": "supportive",
      "timestamp": "2026-03-25T04:00:00+00:00"
    }
  ]
}
```

- `rounds` must be between `1` and `5`.
- Total messages = `rounds x 3` (one per agent per round).
- Agent order is fixed: **USA -> EU -> China**.

---

## Project Structure

```
climate-debate-simulator/
|-- .env.example          # Environment variable template
|-- .gitignore
|-- docker-compose.yml    # Orchestrates api + ollama services
|-- Dockerfile            # Builds the FastAPI app container
|-- requirements.txt      # Python dependencies
|-- main.py               # FastAPI application entry point
|-- agents/
|   +-- debater.py        # DebaterAgent: prompt construction + LLM call
|-- core/
|   +-- rag_service.py    # ChromaDB ingestion + context retrieval
|-- data/
|   +-- policies/
|       |-- usa_policy.json
|       |-- eu_policy.json
|       +-- china_policy.json
|-- static/
|   |-- index.html        # Frontend UI
|   +-- script.js         # Vanilla JS for API interaction
+-- tests/
    +-- test_debate.py    # Unit and integration tests
```

---

## Configuration

| Variable          | Description                           | Default               |
|-------------------|---------------------------------------|-----------------------|
| `OLLAMA_BASE_URL` | URL of the Ollama service             | `http://ollama:11434` |
| `LLM_MODEL_NAME`  | LLM model to use within Ollama        | `llama3:8b`           |

---

## Testing

Run tests with `pytest` inside the container:

```bash
docker-compose exec api pytest tests/ -v
```

Or locally (you must have Python dependencies installed):

```bash
pip install -r requirements.txt
pytest tests/ -v
```

---

## Stopping the Application

```bash
docker-compose down
```

To remove volumes and cached model data:

```bash
docker-compose down -v
```
