# VeritasAgent

Autonomous AI agents are making real decisions — but most platforms give you logs you have to trust.
VeritasAgent creates **cryptographically signed, tamper-evident receipts** for every agent action,
so auditors can verify what happened without trusting the platform.

## How it works

Every tool call an agent makes produces a signed receipt containing:
- What was called, with what inputs, and what it returned
- A SHA-256 hash chained to the previous receipt
- An Ed25519 signature tied to the agent's identity

Tamper any receipt — or delete one — and verification fails with an exact reason.

## Core Features

- Ed25519 digital signatures
- SHA-256 hashing
- RFC 8785 JCS canonicalization (deterministic hashing)
- Receipt chaining via `previous_receipt_hash`
- Multi-agent provenance via `parent_receipt_hash`
- **Live Gemini 1.5 Flash integration** — real tool calls, real signed receipts
- Offline CLI verification with `verify.py`
- Tampering demo with `tamper_demo.py`

## Live Agent Demo (Gemini)

Run a real Gemini agent that signs every tool call as it happens:

```bash
export GEMINI_API_KEY=your_key_here
python gemini_agent.py
```

The agent has access to three tools — `get_weather`, `search_web`, and `calculate`.
Every invocation produces a chained signed receipt persisted to `gemini_receipts.json`.

Verify the receipt chain offline after the fact:

```bash
python gemini_agent.py --verify gemini_receipts.json
```

Output shows each receipt ID, signature validity, and whether the chain is intact —
no backend required.

## Project Structure

```text
secure-ai-agent/
├── backend/
│   ├── main.py          # FastAPI — receipts, chain status, agents
│   └── store.py
├── chain/
│   └── logic.py         # Chain verification logic
├── core/
│   └── crypto.py        # Ed25519 signing, SHA-256, JCS canonicalization
├── middleware/
│   └── interceptor.py   # Intercept and sign agent actions
├── frontend/            # Next.js dashboard
├── gemini_agent.py      # Live Gemini agent with signed receipts
├── tamper_demo.py       # Demonstrates tamper detection
└── verify.py            # Offline CLI verifier
```

## Backend API (FastAPI)

| Endpoint | Description |
|---|---|
| `GET /receipts` | List all receipts |
| `GET /receipts/{id}` | Get one receipt |
| `GET /chain/status` | Full chain verification status |
| `GET /agents` | List agents with receipt counts |
| `POST /demo/failure` | Inject tamper into receipt #3 |
| `POST /demo/reset` | Reset to valid chain |

## Dashboard (Next.js)

- Receipt Chain Timeline
- Chain Integrity Status (hash + signature validity per receipt)
- Tampering Alert Panel
- Edge Case Visualizer
- Receipt Inspector
- Multi-Agent Provenance Graph (React Flow)
- Live Receipt Stream (polls every 2 seconds)

## Setup

### Python backend

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Set `NEXT_PUBLIC_BACKEND_URL` if your backend runs on a different port (default: `http://127.0.0.1:8000`).

## CLI Usage

### Tamper demonstration

```bash
python tamper_demo.py
```

1. Generates 5 receipts
2. Modifies receipt #3
3. Verifies the full chain
4. Prints exactly where and why verification fails

### Offline verification

```bash
python verify.py tampered_chain.json
```

Works on a single receipt or a full chain file.

## Why this matters

Most agent observability tools are just logging — you still have to trust whoever controls the logs.
VeritasAgent makes the receipts self-verifying. Even if the backend is compromised or the logs are
edited, an auditor with only the JSON file and `verify.py` can detect it.

This is the primitive that production agentic systems will need as they move into regulated workflows.
