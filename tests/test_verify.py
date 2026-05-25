from veritasagent.core.crypto import generate_signing_key
from veritasagent.core.schema import ReceiptPayload, SignatureBlock, SignedReceipt
from veritasagent.core.verify import verify_chain, verify_receipt
from veritasagent.core.crypto import hash_json, sign_payload, public_key_hex


def make_receipt(sequence: int, prev: str):
    key = generate_signing_key("1f" * 32)
    payload = ReceiptPayload(
        chain_id="c1",
        agent_id="a1",
        tool_name="t1",
        tool_args_hash="sha256:a",
        result_hash="sha256:b",
        timestamp="2026-01-01T00:00:00+00:00",
        sequence=sequence,
        previous_receipt_hash=prev,
    )
    d = payload.model_dump(exclude_none=True)
    sig = SignatureBlock(sig=sign_payload(d, key), public_key=public_key_hex(key))
    return SignedReceipt(payload=payload, receipt_hash=hash_json(d), signature=sig)


def test_receipt_verifies():
    r = make_receipt(1, "sha256:GENESIS")
    assert verify_receipt(r).ok


def test_chain_detects_deletion():
    r1 = make_receipt(1, "sha256:GENESIS")
    r2 = make_receipt(2, r1.receipt_hash)
    r3 = make_receipt(3, r2.receipt_hash)
    assert not verify_chain([r1, r3]).ok
