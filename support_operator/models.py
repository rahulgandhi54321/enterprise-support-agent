from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TicketCategory(str, Enum):
    billing = "Billing"
    refund = "Refund"
    technical_issue = "Technical issue"
    product_question = "Product question"
    feature_request = "Feature request"
    complaint = "Complaint"
    escalation = "Escalation"
    account_access = "Account access"
    order_status = "Order status"


class Priority(str, Enum):
    low = "Low"
    medium = "Medium"
    high = "High"
    urgent = "Urgent"


class Sentiment(str, Enum):
    positive = "Positive"
    neutral = "Neutral"
    negative = "Negative"
    angry = "Angry"
    distressed = "Distressed"


class EscalationStatus(str, Enum):
    none = "Not escalated"
    human_review = "Human review required"
    security = "Security escalation required"
    legal = "Legal escalation required"
    approval = "Approval required"


class SupportRequest(BaseModel):
    channel: str = Field(description="Incoming channel, such as email, chat, CRM, WhatsApp, Slack, or portal.")
    message: str = Field(min_length=1, description="Customer message to analyze.")
    customer_id: Optional[str] = Field(default=None, description="CRM customer id if known.")
    ticket_id: Optional[str] = Field(default=None, description="Existing ticket id if present.")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ToolAction(BaseModel):
    tool: str
    purpose: str
    status: str
    detail: str


class SupportDecision(BaseModel):
    ticket_category: TicketCategory
    priority: Priority
    sentiment: Sentiment
    suggested_action: str
    draft_reply: str
    escalation_status: EscalationStatus
    confidence_score: float = Field(ge=0, le=1)
    tool_actions_performed: List[ToolAction] = Field(default_factory=list)
    internal_notes: str
    sla_risk: bool
    churn_risk: bool
    vip_customer: bool
    fraud_or_spam_indicators: List[str] = Field(default_factory=list)
    customer_context: Dict[str, Any] = Field(default_factory=dict)
    order_context: Dict[str, Any] = Field(default_factory=dict)
    policy_context: Dict[str, Any] = Field(default_factory=dict)
    audit_summary: str = ""
    runtime_logs: List[str] = Field(default_factory=list)
    api_usage: Dict[str, Any] = Field(default_factory=dict)
    ai_status: str = "not_run"
    model_used: str = ""
    latency_ms: int = 0
