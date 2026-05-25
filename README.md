# VeritasAgent

VeritasAgent is a tamper-evident governance layer for autonomous agent actions.

It creates cryptographically verifiable receipts for each action so auditors do not need to trust platform logs.

## Core Features
- Ed25519 digital signatures
- SHA-256 hashing
- RFC 8785 JCS canonicalization
- Receipt chaining via `previous_receipt_hash`
- Multi-agent provenance via `parent_receipt_hash`
- Offline CLI verification with `verify.py`
- Tampering demo with `tamper_demo.py`

## Project Structure

```text
secure-ai-agent/
├── backend/
│   ├── __init__.py
│   ├── main.py
│   └── store.py
├── chain/
│   ├── __init__.py
│   └── logic.py
├── core/
│   ├── __init__.py
│   └── crypto.py
├── frontend/
│   ├── app/
│   │   ├── components/
│   │   │   └── ui.tsx
│   │   ├── globals.css
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── lib/
│   │   └── types.ts
│   ├── next-env.d.ts
│   ├── next.config.mjs
│   ├── package.json
│   ├── postcss.config.js
│   ├── tailwind.config.js
│   └── tsconfig.json
├── middleware/
│   ├── __init__.py
│   └── interceptor.py
├── requirements.txt
├── tamper_demo.py
└── verify.py
```

## Backend API (FastAPI)
- `GET /receipts` - list all receipts
- `GET /receipts/{id}` - get one receipt
- `GET /chain/status` - full chain verification status
- `GET /agents` - list agents with receipt counts
- `POST /demo/failure` - inject dummy tamper into receipt #3
- `POST /demo/reset` - reset seeded data to valid chain

## Dashboard (Next.js)
The frontend includes:
- Receipt Chain Timeline
- Chain Integrity Status (hash/signature validity per receipt)
- Tampering Alert Panel
- Edge Case Visualizer (failed receipts and reasons)
- Receipt Inspector
- Multi-Agent Provenance Graph (React Flow)
- Live Receipt Stream (polls backend every 2 seconds)

## Setup
### 1) Python backend
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

### 2) Frontend
```bash
cd frontend
npm install
npm run dev
```

If needed, set:
- `NEXT_PUBLIC_BACKEND_URL` (default: `http://127.0.0.1:8000`)

## CLI Usage
### Tamper demonstration
```bash
python tamper_demo.py
```
This script:
1. Generates 5 receipts
2. Modifies receipt #3
3. Verifies the chain
4. Prints exactly where and why verification fails

### Offline verification
```bash
python verify.py tampered_chain.json
```
You can also verify a single receipt JSON.

## Notes
- The current system is a governance and verification layer with seeded demo data.
- The most important next improvement is to plug in a real LLM agent runtime so live tool calls are intercepted and signed in production workflows.
