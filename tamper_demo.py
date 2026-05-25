from __future__ import annotations

import copy
import json

from chain.logic import ReceiptChain, verify_chain
from core.crypto import generate_signing_key


def main() -> None:
    keys = {
        "planner-agent": generate_signing_key("11" * 32),
        "research-agent": generate_signing_key("22" * 32),
        "execution-agent": generate_signing_key("33" * 32),
    }
    chain = ReceiptChain(signing_keys=keys)

    r1 = chain.append_receipt(chain_id="tamper-chain", agent_id="planner-agent", tool_name="plan", args={"task": "t1"}, result={"ok": True})
    r2 = chain.append_receipt(chain_id="tamper-chain", agent_id="research-agent", tool_name="research", args={"doc": "d1"}, result={"ok": True}, parent_receipt_hash=r1.receipt_hash)
    r3 = chain.append_receipt(chain_id="tamper-chain", agent_id="execution-agent", tool_name="execute", args={"step": 1}, result={"ok": True}, parent_receipt_hash=r2.receipt_hash)
    r4 = chain.append_receipt(chain_id="tamper-chain", agent_id="planner-agent", tool_name="review", args={"step": 2}, result={"ok": True}, parent_receipt_hash=r3.receipt_hash)
    r5 = chain.append_receipt(chain_id="tamper-chain", agent_id="execution-agent", tool_name="finalize", args={"step": 3}, result={"ok": True}, parent_receipt_hash=r4.receipt_hash)

    receipts = [r1, r2, r3, r4, r5]

    tampered_receipts = copy.deepcopy(receipts)
    tampered_receipts[2].payload.tool_name = "execute_unauthorized_transfer"

    print("Generated chain length:", len(tampered_receipts))
    print("Tampered receipt: #3")

    result = verify_chain(tampered_receipts)
    if result.ok:
        print("Unexpected: chain still valid")
        return

    print("Chain verification failed.")
    print("Break details:")
    for err in result.errors:
        print(f"- {err}")

    serializable = [r.to_dict() for r in tampered_receipts]
    with open("tampered_chain.json", "w", encoding="utf-8") as f:
        json.dump(serializable, f, indent=2)
    print("Saved tampered chain to tampered_chain.json")


if __name__ == "__main__":
    main()
