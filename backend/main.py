from __future__ import annotations

from collections import Counter
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from chain.logic import verify_chain, verify_receipt
from backend.store import as_signed_receipts, load_receipts, reset_seed_data, save_receipts

app = FastAPI(title="VeritasAgent Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/receipts")
def get_receipts() -> list[dict[str, Any]]:
    rows = load_receipts()
    enriched: list[dict[str, Any]] = []
    for idx, receipt in enumerate(rows, start=1):
        r = dict(receipt)
        r["id"] = idx
        enriched.append(r)
    return enriched


@app.get("/receipts/{receipt_id}")
def get_receipt(receipt_id: int) -> dict[str, Any]:
    rows = load_receipts()
    if receipt_id < 1 or receipt_id > len(rows):
        raise HTTPException(status_code=404, detail="Receipt not found")

    receipt = rows[receipt_id - 1]
    parsed = as_signed_receipts()[receipt_id - 1]
    v = verify_receipt(parsed)
    return {"id": receipt_id, "verification": {"ok": v.ok, "errors": v.errors}, **receipt}


@app.get("/chain/status")
def get_chain_status() -> dict[str, Any]:
    parsed = as_signed_receipts()
    result = verify_chain(parsed)

    per_receipt = []
    for idx, receipt in enumerate(parsed, start=1):
        single = verify_receipt(receipt)
        per_receipt.append(
            {
                "id": idx,
                "sequence": receipt.payload.sequence,
                "agent_id": receipt.payload.agent_id,
                "tool_name": receipt.payload.tool_name,
                "hash_valid": "receipt_hash mismatch" not in " ".join(single.errors),
                "signature_valid": "invalid signature" not in " ".join(single.errors),
                "ok": single.ok,
                "errors": single.errors,
            }
        )

    return {"ok": result.ok, "errors": result.errors, "receipts": per_receipt}


@app.get("/agents")
def get_agents() -> list[dict[str, Any]]:
    parsed = as_signed_receipts()
    counts = Counter([r.payload.agent_id for r in parsed])
    return [{"agent_id": k, "receipt_count": v} for k, v in sorted(counts.items())]


@app.post("/demo/failure")
def inject_dummy_failure() -> dict[str, Any]:
    rows = load_receipts()
    if len(rows) < 3:
        raise HTTPException(status_code=400, detail="Need at least 3 receipts to tamper")

    rows[2]["payload"]["tool_name"] = "execute_unauthorized_transfer"
    save_receipts(rows)
    return {"ok": True, "message": "Dummy failure injected at receipt #3"}


@app.post("/demo/reset")
def reset_demo_data() -> dict[str, Any]:
    reset_seed_data()
    return {"ok": True, "message": "Demo data reset to valid chain"}
