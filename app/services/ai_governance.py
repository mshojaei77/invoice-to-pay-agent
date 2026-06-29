from __future__ import annotations


APPROVED_AI_TOOLS = {
    "liteparse": {
        "tool_type": "document_parser",
        "data_access": ["invoice_documents", "supplier_data"],
        "review_owner": "finance_operations",
        "status": "approved",
    },
    "docling": {
        "tool_type": "document_parser",
        "data_access": ["invoice_documents", "supplier_data"],
        "review_owner": "finance_operations",
        "status": "approved",
    },
    "deterministic_controls": {
        "tool_type": "rules_engine",
        "data_access": ["invoice_metadata", "approval_metadata"],
        "review_owner": "finance_controller",
        "status": "approved",
    },
}


def evaluate_ai_governance(
    parser_route: list[dict],
    parsed_documents: list[dict],
    requires_human_approval: bool,
    approval_route: dict,
) -> dict:
    used_tools = sorted(
        {
            str(route.get("parser", "")).lower()
            for route in parser_route
            if route.get("parser")
        }
        | {"deterministic_controls"}
    )
    unapproved_tools = [tool for tool in used_tools if tool not in APPROVED_AI_TOOLS]

    inventory = [
        {"tool_name": tool, **APPROVED_AI_TOOLS.get(tool, {"status": "unapproved"})}
        for tool in used_tools
    ]

    confidence_values = [
        float(document.get("confidence"))
        for document in parsed_documents
        if isinstance(document.get("confidence"), int | float)
    ]
    min_confidence = min(confidence_values) if confidence_values else None

    guardrails = [
        {
            "control": "approved_tool_inventory",
            "status": "failed" if unapproved_tools else "passed",
            "message": "Every AI or automation component must be inventoried and approved.",
        },
        {
            "control": "human_oversight",
            "status": "passed" if requires_human_approval or approval_route.get("route") == "auto_post" else "review",
            "message": "Medium/high-risk cases require human review; clean low-risk runs may auto-post.",
        },
        {
            "control": "output_traceability",
            "status": "passed",
            "message": "Parser route, risk reasons, approval route, ERP sync plan, and audit events are run-linked.",
        },
        {
            "control": "low_confidence_review",
            "status": "review" if min_confidence is not None and min_confidence < 0.7 else "passed",
            "message": "Low-confidence extraction should be reviewed before expanding automation scope.",
        },
    ]

    return {
        "governance_status": "blocked" if unapproved_tools else "review" if any(item["status"] == "review" for item in guardrails) else "ready",
        "adoption_stage": "stage_3_workflow_automation",
        "approved_tool_inventory": inventory,
        "unapproved_tools": unapproved_tools,
        "shadow_ai_policy": "shut_down_or_formally_adopt",
        "guardrails": guardrails,
    }
