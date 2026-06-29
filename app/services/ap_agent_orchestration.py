from __future__ import annotations


def build_ap_agent_orchestration(
    invoice_capture_plan: dict,
    gl_coding_result: dict,
    match_result: dict,
    fraud_result: dict,
    approval_route: dict,
    payment_execution_plan: dict,
) -> dict:
    agents = [
        {
            "agent": "capture_agent",
            "status": invoice_capture_plan.get("capture_status"),
            "handoff": "coding_agent",
        },
        {
            "agent": "coding_agent",
            "status": gl_coding_result.get("coding_status", "needs_review"),
            "confidence": gl_coding_result.get("confidence"),
            "handoff": "matching_agent",
        },
        {
            "agent": "matching_agent",
            "status": match_result.get("match_status"),
            "handoff": "fraud_agent",
        },
        {
            "agent": "fraud_agent",
            "status": fraud_result.get("fraud_status"),
            "handoff": "approval_agent",
        },
        {
            "agent": "approval_agent",
            "status": approval_route.get("route"),
            "handoff": "payment_agent",
        },
        {
            "agent": "payment_agent",
            "status": payment_execution_plan.get("payment_execution_status"),
            "handoff": "erp_sync",
        },
    ]

    blocked = [
        agent for agent in agents
        if agent.get("status") in {"blocked", "blocked_for_fraud_review", "blocked_until_final_approval", "needs_review"}
    ]

    return {
        "agent_orchestration_status": "blocked" if blocked else "running",
        "autonomy_level": "supervised_end_to_end",
        "agents": agents,
        "blocked_agents": [agent["agent"] for agent in blocked],
    }
