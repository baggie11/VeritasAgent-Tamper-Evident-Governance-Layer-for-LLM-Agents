"""
gemini_agent.py

A self-contained Gemini tool-calling demo that emits tamper-evident receipts
using VeritasAgent's existing crypto utilities.

What it does:
- Uses Google Gemini (`google-generativeai`, model `gemini-1.5-flash`) with tool use.
- Defines tools: `get_weather`, `search_web`, `calculate`.
- Creates signed receipts before and after each tool execution.
- Chains receipts with `previous_receipt_hash`.
- Appends receipts to `gemini_receipts.json`.
- Prints a verification summary at the end.
- Supports offline verification mode:
    python gemini_agent.py --verify gemini_receipts.json

How to run:
1) Set API key:
   - PowerShell: $env:GEMINI_API_KEY="your_key_here"
2) Run agent mode:
   - python gemini_agent.py
3) Run offline verify mode:
   - python gemini_agent.py --verify gemini_receipts.json
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import google.generativeai as genai

from chain.logic import GENESIS_HASH, ReceiptPayload, SignatureBlock, SignedReceipt, verify_chain
from core.crypto import generate_signing_key, hash_json, public_key_hex, sign_payload, verify_signature

AGENT_ID = "gemini-agent-001"
CHAIN_ID = "gemini-agent-chain"
RECEIPTS_FILE = Path("gemini_receipts.json")
SEED_ENV = "VERITAS_AGENT_SEED_HEX"

_call_count = 0
_receipt_sequence = 0
_last_receipt_hash = GENESIS_HASH
_signing_key = None


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_receipts(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a JSON array")
    return data


def _save_receipts(path: Path, receipts: list[dict[str, Any]]) -> None:
    path.write_text(json.dumps(receipts, indent=2), encoding="utf-8")


def _receipt_payload(
    *,
    tool_name: str,
    tool_input: dict[str, Any],
    tool_output: Any,
    previous_receipt_hash: str,
    sequence: int,
) -> dict[str, Any]:
    return {
        "agent_id": AGENT_ID,
        "action_type": "tool_call",
        "tool_name": tool_name,
        "tool_input": tool_input,
        "tool_output": tool_output,
        "timestamp": utc_now_iso(),
        "receipt_id": str(uuid.uuid4()),
        "previous_receipt_hash": previous_receipt_hash,
        "sequence": sequence,
    }


def _build_signed_receipt(payload: dict[str, Any], signing_key) -> dict[str, Any]:
    receipt_hash = hash_json(payload)
    signature = sign_payload(payload, signing_key)
    return {
        "payload": payload,
        "receipt_hash": receipt_hash,
        "signature": {
            "alg": "EdDSA",
            "sig": signature,
            "public_key": public_key_hex(signing_key),
        },
    }


def _append_signed_receipt(*, path: Path, signed_receipt: dict[str, Any]) -> None:
    receipts = _load_receipts(path)
    receipts.append(signed_receipt)
    _save_receipts(path, receipts)


def _record_tool_receipt(tool_name: str, tool_input: dict[str, Any], tool_output: Any) -> dict[str, Any]:
    global _receipt_sequence, _last_receipt_hash

    _receipt_sequence += 1
    payload = _receipt_payload(
        tool_name=tool_name,
        tool_input=tool_input,
        tool_output=tool_output,
        previous_receipt_hash=_last_receipt_hash,
        sequence=_receipt_sequence,
    )
    signed = _build_signed_receipt(payload, _signing_key)
    _append_signed_receipt(path=RECEIPTS_FILE, signed_receipt=signed)
    _last_receipt_hash = signed["receipt_hash"]
    return signed


def _safe_eval_math(expression: str) -> float:
    allowed_nodes = {
        ast.Expression,
        ast.BinOp,
        ast.UnaryOp,
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.Mod,
        ast.Pow,
        ast.USub,
        ast.UAdd,
        ast.Constant,
    }

    tree = ast.parse(expression, mode="eval")
    for node in ast.walk(tree):
        if type(node) not in allowed_nodes:
            raise ValueError("Unsupported expression")
        if isinstance(node, ast.Constant) and not isinstance(node.value, (int, float)):
            raise ValueError("Only numeric constants are allowed")

    return float(eval(compile(tree, "<calc>", "eval"), {"__builtins__": {}}, {}))


def get_weather(city: str) -> dict[str, Any]:
    tool_input = {"city": city}
    _record_tool_receipt("get_weather", tool_input, {"status": "pending"})
    result = {
        "city": city,
        "temperature_c": 27,
        "conditions": "Partly cloudy",
        "source": "mock",
    }
    _record_tool_receipt("get_weather", tool_input, result)
    return result


def search_web(query: str) -> dict[str, Any]:
    tool_input = {"query": query}
    _record_tool_receipt("search_web", tool_input, {"status": "pending"})
    result = {
        "query": query,
        "results": [
            {"title": f"Overview of {query}", "url": "https://example.com/a"},
            {"title": f"Latest on {query}", "url": "https://example.com/b"},
        ],
        "source": "mock",
    }
    _record_tool_receipt("search_web", tool_input, result)
    return result


def calculate(expression: str) -> dict[str, Any]:
    tool_input = {"expression": expression}
    _record_tool_receipt("calculate", tool_input, {"status": "pending"})
    try:
        value = _safe_eval_math(expression)
        result = {"expression": expression, "value": value}
    except Exception as exc:
        result = {"expression": expression, "error": str(exc)}
    _record_tool_receipt("calculate", tool_input, result)
    return result


def _signature_valid(receipt: dict[str, Any]) -> bool:
    payload = receipt["payload"]
    sig = receipt["signature"]["sig"]
    pub = receipt["signature"]["public_key"]
    return verify_signature(payload, sig, pub)


def _to_chain_receipt(receipt: dict[str, Any]) -> SignedReceipt:
    payload = receipt["payload"]
    tool_input = payload.get("tool_input", {})
    tool_output = payload.get("tool_output")

    converted_payload = ReceiptPayload(
        type="agent.tool_call.v1",
        chain_id=CHAIN_ID,
        agent_id=payload["agent_id"],
        tool_name=payload["tool_name"],
        tool_args_hash=hash_json(tool_input if isinstance(tool_input, dict) else {"value": tool_input}),
        result_hash=hash_json({"tool_output": tool_output}),
        timestamp=payload["timestamp"],
        sequence=int(payload["sequence"]),
        previous_receipt_hash=payload["previous_receipt_hash"],
        metadata={"receipt_id": payload["receipt_id"], "action_type": payload["action_type"]},
    )

    sig = receipt["signature"]
    return SignedReceipt(
        payload=converted_payload,
        receipt_hash=receipt["receipt_hash"],
        signature=SignatureBlock(alg=sig["alg"], sig=sig["sig"], public_key=sig["public_key"]),
    )


def verify_receipt_chain_file(path: Path) -> tuple[bool, list[str], list[dict[str, Any]]]:
    receipts = _load_receipts(path)
    errors: list[str] = []

    for idx, receipt in enumerate(receipts, start=1):
        payload = receipt.get("payload", {})
        expected_hash = hash_json(payload)
        if expected_hash != receipt.get("receipt_hash"):
            errors.append(f"receipt #{idx}: receipt_hash mismatch")

        if not _signature_valid(receipt):
            rid = payload.get("receipt_id", f"#{idx}")
            errors.append(f"receipt #{idx} ({rid}): invalid signature")

    chain_receipts = [_to_chain_receipt(r) for r in receipts]
    chain_result = verify_chain(chain_receipts)
    if not chain_result.ok:
        errors.extend(chain_result.errors)

    return len(errors) == 0, errors, receipts


def print_summary(receipts: list[dict[str, Any]]) -> None:
    post_receipts = [r for r in receipts if r.get("payload", {}).get("tool_output", {}).get("status") != "pending"]
    print(f"Tool calls made: {len(post_receipts)}")

    for receipt in receipts:
        rid = receipt["payload"]["receipt_id"]
        ok = _signature_valid(receipt)
        print(f"- receipt_id={rid} signature_valid={ok}")

    chain_ok, chain_errors, _ = verify_receipt_chain_file(RECEIPTS_FILE)
    print(f"Chain intact: {chain_ok}")
    if not chain_ok:
        for err in chain_errors:
            print(f"  * {err}")


def run_agent() -> int:
    global _signing_key, _last_receipt_hash, _receipt_sequence, _call_count

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Missing GEMINI_API_KEY environment variable.")
        return 1

    seed = os.getenv(SEED_ENV)
    _signing_key = generate_signing_key(seed)

    existing = _load_receipts(RECEIPTS_FILE)
    if existing:
        _last_receipt_hash = existing[-1]["receipt_hash"]
        _receipt_sequence = int(existing[-1]["payload"].get("sequence", len(existing)))
    else:
        _last_receipt_hash = GENESIS_HASH
        _receipt_sequence = 0

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        tools=[get_weather, search_web, calculate],
    )
    chat = model.start_chat(enable_automatic_function_calling=True)

    prompt = (
        "Use tools to answer this in one pass: "
        "1) weather in Tokyo, "
        "2) search web for 'tamper evident logs', "
        "3) calculate (15*4)+9."
    )

    response = chat.send_message(prompt)

    all_receipts = _load_receipts(RECEIPTS_FILE)
    post_receipts = [r for r in all_receipts if r.get("payload", {}).get("tool_output", {}).get("status") != "pending"]
    _call_count = len(post_receipts)

    print("Gemini response:")
    print(response.text if hasattr(response, "text") else str(response))
    print("")
    print_summary(all_receipts)
    return 0


def run_verify(path: Path) -> int:
    ok, errors, receipts = verify_receipt_chain_file(path)
    print(f"Receipts loaded: {len(receipts)}")
    for receipt in receipts:
        rid = receipt["payload"]["receipt_id"]
        print(f"- receipt_id={rid} signature_valid={_signature_valid(receipt)}")
    print(f"Chain intact: {ok}")
    if not ok:
        for err in errors:
            print(f"  * {err}")
        return 2
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Gemini agent with VeritasAgent receipts")
    parser.add_argument("--verify", metavar="PATH", help="Offline-verify receipt chain JSON file")
    args = parser.parse_args()

    if args.verify:
        return run_verify(Path(args.verify))
    return run_agent()


if __name__ == "__main__":
    raise SystemExit(main())
