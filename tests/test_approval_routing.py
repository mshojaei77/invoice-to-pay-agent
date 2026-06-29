from app.services.approval_routing import route_approval


def test_routes_clean_low_risk_to_auto_post() -> None:
    result = route_approval(
        risk_level="low",
        risk_score=0.0,
        exception_result={"categories": [], "exceptions": []},
        gl_coding_result={"coding_status": "suggested"},
    )

    assert result["route"] == "auto_post"
    assert result["approver_role"] == "system"


def test_routes_duplicate_control_to_ap_manager() -> None:
    result = route_approval(
        risk_level="high",
        risk_score=100.0,
        exception_result={
            "categories": ["duplicate_control"],
            "exceptions": [{"code": "confirmed_duplicate"}],
        },
    )

    assert result["route"] == "ap_manager_review"
    assert result["approver_role"] == "ap_manager"


def test_routes_three_way_exception_to_buyer_or_receiving_owner() -> None:
    result = route_approval(
        risk_level="medium",
        risk_score=45.0,
        exception_result={
            "categories": ["pricing", "receiving"],
            "exceptions": [{"code": "match:total_mismatch"}],
        },
    )

    assert result["route"] == "buyer_receiving_review"
    assert result["reason"] == "three_way_match_exception"
