from __future__ import annotations

import json
import sys
from pathlib import Path

from veritasagent.core.schema import SignedReceipt
from veritasagent.core.verify import verify_receipt


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/verify.py <receipt.json>")
        return 1

    path = Path(sys.argv[1])
    receipt = SignedReceipt.model_validate(json.loads(path.read_text(encoding="utf-8")))
    result = verify_receipt(receipt)
    if result.ok:
        print("OK: receipt signature and hash are valid")
        return 0

    print("FAILED:")
    for err in result.errors:
        print(f"- {err}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
