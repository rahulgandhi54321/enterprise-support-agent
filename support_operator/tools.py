from __future__ import annotations

import re
from typing import Any, Dict, List

from .audit import log_action
from .mock_data import CRM, ORDERS, POLICIES


def _tool_result(tool: str, purpose: str, status: str, detail: str, data: Dict[str, Any]) -> Dict[str, Any]:
    result = {"tool": tool, "purpose": purpose, "status": status, "detail": detail, "data": data}
    log_action(tool, {"purpose": purpose, "status": status, "detail": detail})
    return result


def query_crm(customer_id: str) -> Dict[str, Any]:
    """Retrieve CRM profile, customer tier, health score, and open ticket summary."""
    customer = CRM.get(customer_id)
    if not customer:
        return _tool_result("query_crm", "Retrieve customer CRM data", "not_found", "No CRM record found.", {})
    return _tool_result("query_crm", "Retrieve customer CRM data", "success", "CRM profile found.", dict(customer))


def retrieve_knowledge(topic: str) -> Dict[str, Any]:
    """Retrieve relevant SOP or policy guidance for a support topic."""
    normalized = topic.lower()
    matches = {key: value for key, value in POLICIES.items() if key in normalized}
    if not matches and ("refund" in normalized or "charge" in normalized):
        matches["refund"] = POLICIES["refund"]
        matches["billing"] = POLICIES["billing"]
    if not matches:
        matches["general"] = "Use verified records only. Escalate when confidence is low or policy is missing."
    return _tool_result("retrieve_knowledge", "Retrieve SOP and policy context", "success", "Knowledge retrieved.", matches)


def check_order_status(message: str) -> Dict[str, Any]:
    """Find and retrieve order or payment status mentioned in a customer message."""
    match = re.search(r"\bORD-\d+\b", message.upper())
    if not match:
        return _tool_result("check_order_status", "Check order/payment status", "not_found", "No order id detected.", {})
    order_id = match.group(0)
    order = ORDERS.get(order_id)
    if not order:
        return _tool_result("check_order_status", "Check order/payment status", "not_found", f"{order_id} was not found.", {"order_id": order_id})
    return _tool_result("check_order_status", "Check order/payment status", "success", f"{order_id} found.", {"order_id": order_id, **order})


def create_or_update_ticket(customer_id: str, category: str, priority: str, summary: str) -> Dict[str, Any]:
    """Create or update a CRM ticket with category, priority, and concise summary."""
    ticket_id = f"TCK-{abs(hash((customer_id, category, summary))) % 9000 + 1000}"
    data = {"ticket_id": ticket_id, "customer_id": customer_id, "category": category, "priority": priority, "summary": summary}
    return _tool_result("create_or_update_ticket", "Create or update CRM ticket", "success", "Ticket record prepared in prototype CRM.", data)


def request_refund_approval(customer_id: str, order_id: str, amount: float, reason: str) -> Dict[str, Any]:
    """Request human approval for a refund. This does not process the refund."""
    data = {"customer_id": customer_id, "order_id": order_id, "amount": amount, "reason": reason, "approval_status": "pending_human_approval"}
    return _tool_result("request_refund_approval", "Request refund approval", "success", "Refund approval request created. No refund was issued.", data)


def notify_human_agent(customer_id: str, reason: str, severity: str) -> Dict[str, Any]:
    """Notify a human support agent for review or escalation."""
    data = {"customer_id": customer_id, "reason": reason, "severity": severity}
    return _tool_result("notify_human_agent", "Notify human agent", "success", "Human review notification prepared.", data)


def schedule_callback(customer_id: str, reason: str, preferred_window: str = "next business day") -> Dict[str, Any]:
    """Schedule a human callback request for a customer."""
    data = {"customer_id": customer_id, "reason": reason, "preferred_window": preferred_window}
    return _tool_result("schedule_callback", "Schedule callback", "success", "Callback request prepared.", data)


def detect_fraud_or_spam(message: str) -> List[str]:
    """Detect simple fraud or spam indicators in the inbound request."""
    lowered = message.lower()
    indicators = []
    if "wire transfer" in lowered or "crypto" in lowered:
        indicators.append("unusual_payment_method")
    if "password" in lowered and ("send" in lowered or "share" in lowered):
        indicators.append("credential_request")
    if len(re.findall(r"https?://", lowered)) > 2:
        indicators.append("multiple_links")
    log_action("detect_fraud_or_spam", {"indicator_count": len(indicators)})
    return indicators
