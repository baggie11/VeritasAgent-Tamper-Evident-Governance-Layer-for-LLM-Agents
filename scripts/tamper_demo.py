from __future__ import annotations

import copy

from veritasagent.core.container import service_scope
from veritasagent.core.verify import verify_chain, verify_receipt
from veritasagent.db.session import SessionLocal, init_db
from veritasagent.storage.receipt_store import ReceiptStore


def run_demo() -> None:
    init_db()
    chain_id = "tamper-demo"

    with service_scope() as service:
        service.create_receipt(chain_id=chain_id, agent_id="planner", tool_name="plan", args={"q": "book"}, result="ok")
        service.create_receipt(chain_id=chain_id, agent_id="research", tool_name="search", args={"x": 1}, result="ok")
        service.create_receipt(chain_id=chain_id, agent_id="exec", tool_name="execute", args={"y": 2}, result="ok")

    db = SessionLocal()
    try:
        receipts = list(ReceiptStore(db).list_chain(chain_id))
    finally:
        db.close()

    print("Original chain valid:", verify_chain(receipts).ok)

    tampered = copy.deepcopy(receipts[1])
    tampered.payload.tool_name = "stolen_funds"
    print("Tampered receipt valid:", verify_receipt(tampered).ok)

    deleted_middle = [receipts[0], receipts[2]]
    print("Chain with deleted middle valid:", verify_chain(deleted_middle).ok)

    replay = receipts + [copy.deepcopy(receipts[1])]
    print("Replay chain valid:", verify_chain(replay).ok)


if __name__ == "__main__":
    run_demo()
