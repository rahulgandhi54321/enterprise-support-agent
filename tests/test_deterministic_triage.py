from support_operator.agent import deterministic_triage
from support_operator.models import SupportRequest


def test_angry_refund_is_high_risk() -> None:
    # cli_enterprise_001 = Sarah Chen, Enterprise Partner (VIP), health_score=42 (churn risk)
    request = SupportRequest(
        channel="email",
        customer_id="cli_enterprise_001",
        message="We received two invoices for ORD-1001 and nobody has responded. Refund us today or we will cancel.",
    )

    result = deterministic_triage(request)

    assert result["ticket_category"] == "Refund"
    assert result["priority"] == "High"
    assert result["sentiment"] == "Angry"
    assert result["churn_risk"] is True
    assert result["vip_customer"] is True
    assert result["escalation_status"] == "Approval required"
    assert len(result["tool_actions_performed"]) >= 5
    assert result["order_context"]["order_id"] == "ORD-1001"


def test_legal_complaint_escalates() -> None:
    request = SupportRequest(
        channel="support_portal",
        customer_id="cli_growth_002",
        message="This is a formal legal complaint.",
    )

    result = deterministic_triage(request)

    assert result["priority"] == "Urgent"
    assert result["escalation_status"] == "Legal escalation required"
    assert result["policy_context"]["legal"]
