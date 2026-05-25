from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from nacl.signing import SigningKey

from core.crypto import hash_json, hash_text, public_key_hex, sign_payload, verify_signature

GENESIS_HASH = "sha256:GENESIS"


@dataclass
class SignatureBlock:
    alg: str
    sig: str
    public_key: str

    def to_dict(self) -> dict[str, Any]:
        return {"alg": self.alg, "sig": self.sig, "public_key": self.public_key}


@dataclass
class ReceiptPayload:
    type: str
    chain_id: str
    agent_id: str
    tool_name: str
    tool_args_hash: str
    result_hash: str
    timestamp: str
    sequence: int
    previous_receipt_hash: str
    policy_id: str | None = None
    policy_decision: str | None = None
    parent_receipt_hash: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = {
            "type": self.type,
            "chain_id": self.chain_id,
            "agent_id": self.agent_id,
            "tool_name": self.tool_name,
            "tool_args_hash": self.tool_args_hash,
            "result_hash": self.result_hash,
            "timestamp": self.timestamp,
            "sequence": self.sequence,
            "previous_receipt_hash": self.previous_receipt_hash,
            "metadata": self.metadata,
        }
        if self.policy_id is not None:
            data["policy_id"] = self.policy_id
        if self.policy_decision is not None:
            data["policy_decision"] = self.policy_decision
        if self.parent_receipt_hash is not None:
            data["parent_receipt_hash"] = self.parent_receipt_hash
        return data


@dataclass
class SignedReceipt:
    payload: ReceiptPayload
    receipt_hash: str
    signature: SignatureBlock

    def to_dict(self) -> dict[str, Any]:
        return {
            "payload": self.payload.to_dict(),
            "receipt_hash": self.receipt_hash,
            "signature": self.signature.to_dict(),
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "SignedReceipt":
        payload = ReceiptPayload(**data["payload"])
        signature = SignatureBlock(**data["signature"])
        return SignedReceipt(payload=payload, receipt_hash=data["receipt_hash"], signature=signature)


@dataclass
class VerificationResult:
    ok: bool
    errors: list[str]


class ReceiptChain:
    def __init__(self, signing_keys: dict[str, SigningKey]):
        self.signing_keys = signing_keys
        self.receipts: list[SignedReceipt] = []

    def append_receipt(
        self,
        *,
        chain_id: str,
        agent_id: str,
        tool_name: str,
        args: dict[str, Any],
        result: Any,
        policy_id: str | None = None,
        policy_decision: str | None = None,
        parent_receipt_hash: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SignedReceipt:
        if agent_id not in self.signing_keys:
            raise ValueError(f"Missing signing key for agent_id '{agent_id}'")

        last = self.receipts[-1] if self.receipts else None
        payload = ReceiptPayload(
            type="agent.tool_call.v1",
            chain_id=chain_id,
            agent_id=agent_id,
            tool_name=tool_name,
            tool_args_hash=hash_json(args),
            result_hash=hash_text(str(result)),
            timestamp=datetime.now(timezone.utc).isoformat(),
            sequence=(last.payload.sequence + 1) if last else 1,
            previous_receipt_hash=last.receipt_hash if last else GENESIS_HASH,
            policy_id=policy_id,
            policy_decision=policy_decision,
            parent_receipt_hash=parent_receipt_hash,
            metadata=metadata or {},
        )

        payload_dict = payload.to_dict()
        key = self.signing_keys[agent_id]
        receipt = SignedReceipt(
            payload=payload,
            receipt_hash=hash_json(payload_dict),
            signature=SignatureBlock(
                alg="EdDSA",
                sig=sign_payload(payload_dict, key),
                public_key=public_key_hex(key),
            ),
        )
        self.receipts.append(receipt)
        return receipt


def verify_receipt(receipt: SignedReceipt) -> VerificationResult:
    errors: list[str] = []
    payload = receipt.payload.to_dict()

    if hash_json(payload) != receipt.receipt_hash:
        errors.append("receipt_hash mismatch: payload no longer matches recorded hash")

    if not verify_signature(payload, receipt.signature.sig, receipt.signature.public_key):
        errors.append("invalid signature: payload was changed after signing or wrong public key")

    return VerificationResult(ok=len(errors) == 0, errors=errors)


def verify_chain(receipts: list[SignedReceipt]) -> VerificationResult:
    errors: list[str] = []
    expected_previous = GENESIS_HASH
    expected_sequence = 1

    for index, receipt in enumerate(receipts, start=1):
        receipt_result = verify_receipt(receipt)
        if not receipt_result.ok:
            for reason in receipt_result.errors:
                errors.append(f"receipt #{index} (sequence {receipt.payload.sequence}): {reason}")

        if receipt.payload.previous_receipt_hash != expected_previous:
            errors.append(
                f"receipt #{index} (sequence {receipt.payload.sequence}): chain link mismatch "
                f"expected previous_receipt_hash={expected_previous}, "
                f"got={receipt.payload.previous_receipt_hash}"
            )

        if receipt.payload.sequence != expected_sequence:
            errors.append(
                f"receipt #{index}: sequence mismatch expected={expected_sequence}, got={receipt.payload.sequence}"
            )

        expected_previous = receipt.receipt_hash
        expected_sequence += 1

    return VerificationResult(ok=len(errors) == 0, errors=errors)
