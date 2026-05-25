from __future__ import annotations

from veritasagent.core.container import service_scope
from veritasagent.db.session import init_db


def run() -> None:
    init_db()
    chain_id = "multi-agent-workflow"

    with service_scope() as service:
        planner = service.create_receipt(
            chain_id=chain_id,
            agent_id="planner-agent",
            tool_name="decompose_task",
            args={"task": "quarterly vendor payment"},
            result={"steps": ["check policy", "validate invoice", "execute payment"]},
            policy_id="finance-policy-v3",
            policy_decision="allow",
        )

        research = service.create_receipt(
            chain_id=chain_id,
            agent_id="research-agent",
            tool_name="fetch_invoice",
            args={"invoice_id": "INV-2026-041"},
            result={"amount": 1200, "currency": "USD"},
            parent_receipt_hash=planner.receipt_hash,
            policy_id="finance-policy-v3",
            policy_decision="allow",
        )

        execution = service.create_receipt(
            chain_id=chain_id,
            agent_id="execution-agent",
            tool_name="execute_payment",
            args={"invoice_id": "INV-2026-041", "amount": 1200},
            result={"tx_id": "TX-7781"},
            parent_receipt_hash=research.receipt_hash,
            policy_id="finance-policy-v3",
            policy_decision="allow",
        )

    print("Planner receipt:", planner.receipt_hash)
    print("Research receipt:", research.receipt_hash)
    print("Execution receipt:", execution.receipt_hash)


if __name__ == "__main__":
    run()
