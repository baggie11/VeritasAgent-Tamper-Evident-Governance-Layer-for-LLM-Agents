from __future__ import annotations

from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable

from chain.logic import ReceiptChain, SignedReceipt


@dataclass
class GovernanceContext:
    chain: ReceiptChain


def secure_tool(
    context: GovernanceContext,
    *,
    chain_id: str,
    agent_id: str,
    policy_id: str | None = None,
    policy_decision: str | None = None,
    parent_receipt_hash: str | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., dict[str, Any]]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., dict[str, Any]]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> dict[str, Any]:
            result = func(*args, **kwargs)
            receipt = context.chain.append_receipt(
                chain_id=chain_id,
                agent_id=agent_id,
                tool_name=func.__name__,
                args={"args": args, "kwargs": kwargs},
                result=result,
                policy_id=policy_id,
                policy_decision=policy_decision,
                parent_receipt_hash=parent_receipt_hash,
            )
            return {"result": result, "receipt": receipt.to_dict()}

        return wrapper

    return decorator
