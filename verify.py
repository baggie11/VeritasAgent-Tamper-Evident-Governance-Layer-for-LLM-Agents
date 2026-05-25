from __future__ import annotations

import json
import sys
from pathlib import Path

from chain.logic import SignedReceipt, verify_chain, verify_receipt


def _load_receipt(path: Path) -> SignedReceipt:
    data = json.loads(path.read_text(encoding="utf-8"))
    return SignedReceipt.from_dict(data)


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python verify.py <receipt.json | receipt_chain.json>")
        return 1

    path = Path(sys.argv[1])
    data = json.loads(path.read_text(encoding="utf-8"))

    if isinstance(data, list):
        receipts = [SignedReceipt.from_dict(item) for item in data]
        result = verify_chain(receipts)
        if result.ok:
            print("OK: chain is valid")
            return 0
        print("FAILED: chain verification failed")
        for err in result.errors:
            print(f"- {err}")
        return 2

    receipt = SignedReceipt.from_dict(data)
    result = verify_receipt(receipt)
    if result.ok:
        print("OK: receipt signature and hash are valid")
        return 0
    print("FAILED: receipt verification failed")
    for err in result.errors:
        print(f"- {err}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
