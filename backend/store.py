from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from chain.logic import ReceiptChain, SignedReceipt
from core.crypto import generate_signing_key

DATA_PATH = Path("backend/data/receipts.json")


def _seed_chain() -> list[dict[str, Any]]:
    keys = {
        "planner-agent": generate_signing_key("11" * 32),
        "research-agent": generate_signing_key("22" * 32),
        "execution-agent": generate_signing_key("33" * 32),
    }
    chain = ReceiptChain(signing_keys=keys)
    r1 = chain.append_receipt(chain_id="live-chain", agent_id="planner-agent", tool_name="plan", args={"task": "vendor payout"}, result={"ok": True})
    r2 = chain.append_receipt(chain_id="live-chain", agent_id="research-agent", tool_name="fetch_invoice", args={"invoice_id": "INV-1"}, result={"ok": True}, parent_receipt_hash=r1.receipt_hash)
    r3 = chain.append_receipt(chain_id="live-chain", agent_id="execution-agent", tool_name="execute_payment", args={"invoice_id": "INV-1"}, result={"tx": "TX-1"}, parent_receipt_hash=r2.receipt_hash)
    r4 = chain.append_receipt(chain_id="live-chain", agent_id="planner-agent", tool_name="review", args={"tx": "TX-1"}, result={"ok": True}, parent_receipt_hash=r3.receipt_hash)
    r5 = chain.append_receipt(chain_id="live-chain", agent_id="execution-agent", tool_name="finalize", args={"tx": "TX-1"}, result={"done": True}, parent_receipt_hash=r4.receipt_hash)
    return [r.to_dict() for r in [r1, r2, r3, r4, r5]]


def ensure_data_file() -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not DATA_PATH.exists():
        DATA_PATH.write_text(json.dumps(_seed_chain(), indent=2), encoding="utf-8")


def load_receipts() -> list[dict[str, Any]]:
    ensure_data_file()
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def save_receipts(receipts: list[dict[str, Any]]) -> None:
    DATA_PATH.write_text(json.dumps(receipts, indent=2), encoding="utf-8")


def as_signed_receipts() -> list[SignedReceipt]:
    return [SignedReceipt.from_dict(r) for r in load_receipts()]


def reset_seed_data() -> None:
    save_receipts(_seed_chain())
