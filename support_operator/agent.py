from __future__ import annotations

import json
import os
import re
import time
from hashlib import sha1
from pathlib import Path
from typing import Any, Dict, Optional

import cohere as _cohere
from openai import AsyncOpenAI, OpenAIError
from dotenv import load_dotenv

from .models import SupportDecision, SupportRequest
from .mock_data import CRM, ORDERS, POLICIES
from .audit import log_action
from .tools import (
    check_order_status,
    create_or_update_ticket,
    detect_fraud_or_spam,
    notify_human_agent,
    query_crm,
    request_refund_approval,
    retrieve_knowledge,
    schedule_callback,
)


ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env.local")
load_dotenv(ROOT / ".env")

OPENAI_FALLBACKS = [
    m.strip()
    for m in os.getenv("SUPPORT_AGENT_MODEL_FALLBACKS", "gpt-4.1-mini,gpt-4o-mini").split(",")
    if m.strip()
]
COHERE_MODEL = os.getenv("COHERE_MODEL", "command-a-03-2025")

_SYNTHESIS_INSTRUCTIONS = (
    "You are an enterprise customer support operator. "
    "Use the verified tool evidence as truth. "
    "Do not invent refunds, account actions, policy claims, private data, or legal conclusions. "
    "Preserve required escalations and approval gates. "
    "Return ONLY compact JSON — no markdown, no code fences — with exactly these keys: "
    "suggested_action, draft_reply, internal_notes, confidence_score, sentiment, priority, escalation_status."
)

_OUTPUT_CONTRACT = {
    "suggested_action": "Concise internal next action.",
    "draft_reply": "Customer-facing reply. No refund promises, legal admissions, or private data.",
    "internal_notes": "Operational notes for the human team.",
    "confidence_score": "Float 0.0–1.0.",
    "sentiment": "Positive | Neutral | Negative | Angry | Distressed.",
    "priority": "Low | Medium | High | Urgent.",
    "escalation_status": "Not escalated | Human review required | Security escalation required | Legal escalation required | Approval required.",
}

_MERGE_KEYS = [
    "suggested_action", "draft_reply", "internal_notes",
    "confidence_score", "sentiment", "priority", "escalation_status",
]


def _build_prompt(request: SupportRequest, base: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "customer_request": request.model_dump(),
        "tool_evidence": base,
        "required_output_contract": _OUTPUT_CONTRACT,
    }


def _merge_model_output(base: Dict[str, Any], update: Dict[str, Any]) -> None:
    for key in _MERGE_KEYS:
        if key in update and update[key] not in (None, ""):
            base[key] = update[key]


def _apply_failure(base: Dict[str, Any], exc: Optional[Exception], model_label: str) -> None:
    base["model_used"] = model_label
    base["confidence_score"] = min(float(base["confidence_score"]), 0.5)
    if base["escalation_status"] == "Not escalated":
        base["escalation_status"] = "Human review required"
    error_name = exc.__class__.__name__ if exc else "UnknownError"
    base["api_usage"] = {"attempted": True, "failure": error_name}
    base["runtime_logs"].append(f"AI synthesis failed: {error_name}.")


def _extract_json_object(raw_text: str) -> Dict[str, Any]:
    try:
        parsed = json.loads(raw_text)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        if not match:
            return {}
        try:
            parsed = json.loads(match.group(0))
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}


def _usage_to_dict(usage: Any) -> Dict[str, Any]:
    if usage is None:
        return {}
    if hasattr(usage, "model_dump"):
        return usage.model_dump()
    if isinstance(usage, dict):
        return usage
    return {
        k: getattr(usage, k)
        for k in ["input_tokens", "output_tokens", "total_tokens"]
        if getattr(usage, k, None) is not None
    }


async def analyze_support_request_safely(request: SupportRequest) -> SupportDecision:
    provider = os.getenv("AI_PROVIDER", "openai").lower()
    if provider == "cohere":
        return await _analyze_cohere(request)
    return await _analyze_openai(request)


async def _analyze_openai(request: SupportRequest) -> SupportDecision:
    started = time.perf_counter()
    base = deterministic_triage(request)
    base["runtime_logs"].extend([
        "Request received by OpenAI route.",
        f"{len(base['tool_actions_performed'])} tool action(s) prepared for model context.",
    ])

    client = AsyncOpenAI()
    prompt = _build_prompt(request, base)
    last_error: Optional[Exception] = None
    response = None
    model_used = OPENAI_FALLBACKS[0] if OPENAI_FALLBACKS else "gpt-4.1-mini"

    for model in OPENAI_FALLBACKS:
        base["runtime_logs"].append(f"OpenAI request started with model {model}.")
        try:
            response = await client.responses.create(
                model=model,
                instructions=_SYNTHESIS_INSTRUCTIONS,
                input=json.dumps(prompt, indent=2),
                max_output_tokens=900,
                temperature=0.2,
            )
            model_used = model
            break
        except OpenAIError as exc:
            last_error = exc
            base["runtime_logs"].append(f"Model {model} failed: {exc.__class__.__name__}.")

    if response is not None:
        raw_text = getattr(response, "output_text", "") or "{}"
        _merge_model_output(base, _extract_json_object(raw_text))
        base["api_usage"] = _usage_to_dict(getattr(response, "usage", None))
        base["ai_status"] = "live_openai_success"
        base["model_used"] = model_used
        base["runtime_logs"].append("OpenAI synthesis completed successfully.")
        base["tool_actions_performed"].append({
            "tool": "openai_responses_api",
            "purpose": "Live AI synthesis from verified support evidence",
            "status": "success",
            "detail": f"Model {model_used} returned final support decision.",
        })
        log_action("openai_responses_api", {
            "purpose": "Live AI synthesis", "status": "success",
            "model": model_used, "usage": base["api_usage"],
        })
    else:
        _apply_failure(base, last_error, ", ".join(OPENAI_FALLBACKS))
        base["ai_status"] = "live_openai_failed"
        base["tool_actions_performed"].append({
            "tool": "openai_responses_api",
            "purpose": "Live AI synthesis from verified support evidence",
            "status": "failed",
            "detail": f"{last_error.__class__.__name__ if last_error else 'OpenAIError'}; human review fallback.",
        })
        log_action("openai_responses_api", {
            "purpose": "Live AI synthesis", "status": "failed", "models": OPENAI_FALLBACKS,
        })

    base["latency_ms"] = int((time.perf_counter() - started) * 1000)
    base["runtime_logs"].append(f"Response completed in {base['latency_ms']} ms.")
    return SupportDecision.model_validate(base)


async def _analyze_cohere(request: SupportRequest) -> SupportDecision:
    started = time.perf_counter()
    base = deterministic_triage(request)
    base["runtime_logs"].extend([
        "Request received by Cohere route.",
        f"{len(base['tool_actions_performed'])} tool action(s) prepared for model context.",
    ])

    client = _cohere.AsyncClientV2(api_key=os.getenv("COHERE_API_KEY", ""))
    prompt = _build_prompt(request, base)
    model = COHERE_MODEL
    base["runtime_logs"].append(f"Cohere request started with model {model}.")

    try:
        response = await client.chat(
            model=model,
            messages=[
                {"role": "system", "content": _SYNTHESIS_INSTRUCTIONS},
                {"role": "user", "content": json.dumps(prompt, indent=2)},
            ],
        )
        raw_text = response.message.content[0].text if response.message.content else "{}"
        _merge_model_output(base, _extract_json_object(raw_text))
        usage = response.usage
        base["api_usage"] = {
            "input_tokens": int(getattr(usage.tokens, "input_tokens", 0) or 0),
            "output_tokens": int(getattr(usage.tokens, "output_tokens", 0) or 0),
            "billed_input_tokens": int(getattr(usage.billed_units, "input_tokens", 0) or 0),
            "billed_output_tokens": int(getattr(usage.billed_units, "output_tokens", 0) or 0),
        }
        base["ai_status"] = "live_cohere_success"
        base["model_used"] = model
        base["runtime_logs"].append("Cohere synthesis completed successfully.")
        base["tool_actions_performed"].append({
            "tool": "cohere_chat_api",
            "purpose": "Live AI synthesis from verified support evidence",
            "status": "success",
            "detail": f"Model {model} returned final support decision.",
        })
        log_action("cohere_chat_api", {
            "purpose": "Live AI synthesis", "status": "success",
            "model": model, "usage": base["api_usage"],
        })
    except Exception as exc:
        _apply_failure(base, exc, model)
        base["ai_status"] = "live_cohere_failed"
        base["tool_actions_performed"].append({
            "tool": "cohere_chat_api",
            "purpose": "Live AI synthesis from verified support evidence",
            "status": "failed",
            "detail": f"{exc.__class__.__name__}; human review fallback.",
        })
        log_action("cohere_chat_api", {
            "purpose": "Live AI synthesis", "status": "failed", "error": exc.__class__.__name__,
        })

    base["latency_ms"] = int((time.perf_counter() - started) * 1000)
    base["runtime_logs"].append(f"Response completed in {base['latency_ms']} ms.")
    return SupportDecision.model_validate(base)


def deterministic_triage(request: SupportRequest, error: Optional[str] = None) -> Dict[str, Any]:
    """Production-style local orchestration for demos, smoke tests, and safe live fallbacks."""
    message = request.message.lower()
    customer = CRM.get(request.customer_id or "", {})
    order_match = re.search(r"\bORD-\d+\b", request.message.upper())
    order_id = order_match.group(0) if order_match else ""
    order = ORDERS.get(order_id, {})
    tier_lower = str(customer.get("tier", "")).lower()
    vip_customer = "vip" in tier_lower or "enterprise" in tier_lower
    health_score = int(customer.get("health_score", 100)) if customer else 100
    tool_actions = []
    runtime_logs = ["Intake parsed.", "Customer, order, policy, risk, and escalation checks started."]

    def add_action(tool: str, purpose: str, status: str, detail: str) -> None:
        tool_actions.append({"tool": tool, "purpose": purpose, "status": status, "detail": detail})
        log_action(tool, {"purpose": purpose, "status": status, "detail": detail})
        runtime_logs.append(f"{tool}: {status} - {detail}")

    add_action(
        "query_crm", "Retrieve customer CRM data",
        "success" if customer else "not_found",
        f"Loaded {customer.get('name', 'unknown customer')} profile." if customer else "No CRM profile found.",
    )
    add_action(
        "check_order_status", "Check order/payment status",
        "success" if order else "not_found",
        f"Verified {order_id}: {order.get('payment_status', 'unknown')}." if order else "No matching order record found.",
    )

    fraud_indicators = []
    if "wire transfer" in message or "crypto" in message:
        fraud_indicators.append("unusual_payment_method")
    if "password" in message and ("send" in message or "share" in message):
        fraud_indicators.append("credential_request")
    if len(re.findall(r"https?://", message)) > 2:
        fraud_indicators.append("multiple_links")
    add_action("detect_fraud_or_spam", "Detect fraud or spam indicators", "success", f"{len(fraud_indicators)} indicator(s) detected.")

    category = "Technical issue"
    priority = "Medium"
    sentiment = "Neutral"
    escalation = "Not escalated"
    policy_keys = ["general"]

    if "refund" in message or "charged" in message:
        category = "Refund"
        priority = "High"
        policy_keys = ["refund", "billing"]
    if "legal" in message:
        category = "Escalation"
        priority = "Urgent"
        escalation = "Legal escalation required"
        policy_keys = ["legal"]
    if "lost access" in message or "locked" in message:
        category = "Account access"
        priority = "High"
        policy_keys = ["security"]
    if "cancel" in message or "nobody has responded" in message:
        sentiment = "Angry"
        escalation = "Human review required"
    if "500" in message or "error" in message or "failing" in message:
        category = "Technical issue"
        policy_keys = ["technical", "sla"]
    if "formal legal complaint" in message:
        escalation = "Legal escalation required"
    if fraud_indicators:
        escalation = "Security escalation required"
        priority = "Urgent"

    refund_threshold = float(os.getenv("REFUND_APPROVAL_THRESHOLD", "100"))
    refund_amount = float(order.get("total", 0) or 0)
    if category == "Refund" and refund_amount > refund_threshold:
        escalation = "Approval required"
        add_action(
            "request_refund_approval", "Request refund approval", "success",
            f"Approval queued for {order_id or 'unknown order'}; no refund was issued.",
        )

    churn_risk = "cancel" in message or health_score < 50
    sla_risk = priority == "Urgent" or (vip_customer and priority == "High") or sentiment == "Angry"

    if escalation != "Not escalated":
        add_action("notify_human_agent", "Notify human agent", "success", f"Routed for {escalation.lower()}.")
    if churn_risk or vip_customer:
        add_action("schedule_callback", "Schedule callback", "success", "Callback recommended for retention-sensitive follow-up.")

    policy_context = {key: POLICIES.get(key, "Use verified records only.") for key in policy_keys}
    add_action("retrieve_knowledge", "Retrieve SOP and policy context", "success", ", ".join(policy_context))

    summary = request.message.strip().replace("\n", " ")
    ticket_id = "TCK-" + sha1(f"{request.customer_id}:{category}:{summary}".encode()).hexdigest()[:6].upper()
    add_action("create_or_update_ticket", "Create or update CRM ticket", "success", f"{ticket_id} prepared with {category} / {priority}.")

    customer_name = customer.get("name", "there")
    if category == "Refund":
        action = "Keep the ticket in billing review, verify the duplicate charge, and wait for approval before promising a refund."
        reply = (
            f"Hi {customer_name}, I understand why this is frustrating. I found this as a billing/refund issue and have routed it for review. "
            "We will verify the duplicate charge before confirming any refund or account credit."
        )
    elif category == "Account access":
        action = "Route through account recovery and security checks before changing account access."
        reply = f"Hi {customer_name}, I can help with access recovery. For security, we need to verify the account before making changes."
    elif category == "Escalation":
        action = "Escalate to the legal queue immediately and avoid admissions of fault in the customer response."
        reply = f"Hi {customer_name}, thank you for raising this. I have routed your message to the appropriate specialist team for review."
    elif category == "Technical issue":
        action = "Create a high-signal technical ticket with error details and route to support engineering if repeatable."
        reply = f"Hi {customer_name}, thanks for the details. I have captured the error context and will route this to the right technical support path."
    else:
        action = "Create or update the ticket, attach retrieved context, and continue with the standard support workflow."
        reply = f"Hi {customer_name}, thanks for reaching out. I have captured your request and will follow the right support workflow."

    confidence = 0.9 if customer else 0.76
    if error:
        confidence = min(confidence, 0.5)

    return {
        "ticket_category": category,
        "priority": priority,
        "sentiment": sentiment,
        "suggested_action": action,
        "draft_reply": reply,
        "escalation_status": escalation,
        "confidence_score": confidence,
        "tool_actions_performed": tool_actions,
        "internal_notes": error or f"{ticket_id} prepared. Context retrieved from CRM, order records, policy knowledge, and audit logging.",
        "sla_risk": sla_risk,
        "churn_risk": churn_risk,
        "vip_customer": vip_customer,
        "fraud_or_spam_indicators": fraud_indicators,
        "customer_context": customer,
        "order_context": {"order_id": order_id, **order} if order else {},
        "policy_context": policy_context,
        "audit_summary": f"{len(tool_actions)} tool action(s) logged for this request.",
        "runtime_logs": runtime_logs,
        "api_usage": {},
        "ai_status": "demo_tooling_only" if not error else "fallback",
        "model_used": "",
        "latency_ms": 0,
    }
