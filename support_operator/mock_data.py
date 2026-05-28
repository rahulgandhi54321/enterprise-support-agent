from __future__ import annotations

CRM = {
    "cli_enterprise_001": {
        "name": "Sarah Chen",
        "company": "Universal Music Group",
        "tier": "Enterprise Partner",
        "account_status": "Active",
        "plan": "AI Transformation Suite",
        "vertical": "Media & Entertainment",
        "health_score": 42,
        "open_tickets": ["TCK-UMG01"],
        "preferred_tone": "Direct and professional",
    },
    "cli_growth_002": {
        "name": "Dr. Marcus Reid",
        "company": "Remoni Health",
        "tier": "Growth",
        "account_status": "Active",
        "plan": "Foundation + Consultancy",
        "vertical": "Healthcare",
        "health_score": 74,
        "open_tickets": [],
        "preferred_tone": "Friendly",
    },
    "cli_starter_003": {
        "name": "Priya Nair",
        "company": "EduBridge Academy",
        "tier": "Starter",
        "account_status": "Active",
        "plan": "AI Native Consultants Course",
        "vertical": "Education",
        "health_score": 61,
        "open_tickets": [],
        "preferred_tone": "Friendly",
    },
}

ORDERS = {
    "ORD-1001": {
        "status": "Active",
        "total": 48000.00,
        "currency": "USD",
        "payment_status": "Possible duplicate invoice",
        "refund_eligible": True,
        "service": "AI-First Call Center — 90-day deployment",
    },
    "ORD-2002": {
        "status": "Delivered",
        "total": 4800.00,
        "currency": "USD",
        "payment_status": "Paid",
        "refund_eligible": False,
        "service": "Foundation Course: AI Native Consultants",
    },
}

POLICIES = {
    "refund": (
        "Course refunds are available within 7 days of purchase if no sessions have been attended. "
        "Consulting engagement refunds above $5,000 require Partner-level approval before any commitment is made."
    ),
    "billing": (
        "Billing disputes on retainers or project invoices require invoice verification within 14 days of issuance. "
        "Duplicate charges are investigated and resolved within 5 business days."
    ),
    "technical": (
        "FSZT Labs product failures (AI-First Call Center, Discovery Agents, Omnichannel Super Agents, etc.) "
        "are P1 issues — collect reproduction steps, system version, and client environment, then escalate to engineering."
    ),
    "security": (
        "Any PII exposure, credential leak, or data incident in a deployed AI system must be escalated to the "
        "FSZT security team immediately. Do not attempt resolution without security sign-off."
    ),
    "legal": (
        "IP disputes, contract breaches, or formal legal complaints must be escalated to legal. "
        "Do not admit liability or make commitments on behalf of FSZT Partners."
    ),
    "sla": (
        "Enterprise Partners: 4-hour response SLA. "
        "Growth clients: 24-hour SLA. "
        "Starter clients: 48-hour SLA. "
        "VIP Enterprise accounts are flagged for immediate escalation."
    ),
    "onboarding": (
        "New Enterprise clients are assigned a Forward Deployed Engineer within 5 business days of contract signing. "
        "Growth clients are onboarded via structured sessions within 10 days."
    ),
    "labs": (
        "FSZT Labs products (AI Sales Stack, Voice-to-Code, Pitch Agents, AI Sales Coach) follow the standard "
        "product SLA. Critical bugs blocking client workflows are P0 and require same-day escalation."
    ),
    "general": (
        "FSZT Partners builds and ships AI-native systems. All support decisions must be grounded in verified "
        "client data, engagement records, and policy — never in assumptions. Escalate when uncertain."
    ),
}
