from __future__ import annotations

import base64
import hashlib
from typing import Any

import jcs
from nacl.encoding import HexEncoder
from nacl.signing import SigningKey, VerifyKey


def canonicalize(payload: dict[str, Any]) -> bytes:
    return jcs.canonicalize(payload)


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_json(payload: dict[str, Any]) -> str:
    return f"sha256:{sha256_hex(canonicalize(payload))}"


def hash_text(text: str) -> str:
    return f"sha256:{sha256_hex(text.encode('utf-8'))}"


def generate_signing_key(seed_hex: str | None = None) -> SigningKey:
    if seed_hex:
        return SigningKey(seed_hex, encoder=HexEncoder)
    return SigningKey.generate()


def public_key_hex(signing_key: SigningKey) -> str:
    return signing_key.verify_key.encode(encoder=HexEncoder).decode("ascii")


def sign_payload(payload: dict[str, Any], signing_key: SigningKey) -> str:
    signed = signing_key.sign(canonicalize(payload))
    return base64.b64encode(signed.signature).decode("ascii")


def verify_signature(payload: dict[str, Any], signature_b64: str, public_key_hex_value: str) -> bool:
    verify_key = VerifyKey(public_key_hex_value, encoder=HexEncoder)
    signature = base64.b64decode(signature_b64)
    try:
        verify_key.verify(canonicalize(payload), signature)
        return True
    except Exception:
        return False
