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
        "health_trend": "declining",
        "renewal_date": "2025-09-01",
        "open_tickets": ["TCK-UMG01"],
        "preferred_tone": "Direct and professional",
        "cs_note": "Health score dropped 18 pts in 30 days. Duplicate invoice dispute unresolved. High churn risk.",
    },
    "cli_growth_002": {
        "name": "Dr. Marcus Reid",
        "company": "Remoni Health",
        "tier": "Growth",
        "account_status": "Active",
        "plan": "Foundation + Consultancy",
        "vertical": "Healthcare",
        "health_score": 74,
        "health_trend": "stable",
        "renewal_date": "2026-01-15",
        "open_tickets": [],
        "preferred_tone": "Friendly",
        "cs_note": "Expansion signal: asked about AI Sales Stack last QBR. Healthy account, good engagement.",
    },
    "cli_starter_003": {
        "name": "Priya Nair",
        "company": "EduBridge Academy",
        "tier": "Starter",
        "account_status": "Active",
        "plan": "AI Native Consultants Course",
        "vertical": "Education",
        "health_score": 61,
        "health_trend": "stable",
        "renewal_date": "2025-11-30",
        "open_tickets": [],
        "preferred_tone": "Friendly",
        "cs_note": "Onboarding in progress. SSO migration caused access issues. Cohort starts soon — urgent.",
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
        "Consulting engagement refunds or credits above $5,000 require Partner-level approval before any commitment is made. "
        "The AI Customer Success Agent must flag high-value refund requests and never promise resolution without approval."
    ),
    "billing": (
        "Billing disputes on retainers or project invoices require invoice verification within 14 days of issuance. "
        "Duplicate charges are investigated and resolved within 5 business days. "
        "The CS agent should acknowledge the dispute immediately, log it, and confirm next steps with a timeline."
    ),
    "technical": (
        "FSZT Labs product failures (AI-First Call Center, Discovery Agents, Omnichannel Super Agents, etc.) "
        "are P1 issues — collect reproduction steps, system version, and client environment, then escalate to engineering. "
        "The CS agent must communicate status updates proactively until resolved."
    ),
    "security": (
        "Any PII exposure, credential leak, or data incident in a deployed AI system must be escalated to the "
        "FSZT security team immediately. Do not attempt resolution without security sign-off. "
        "Treat all security signals as critical — a compromised AI deployment is a reputational risk."
    ),
    "legal": (
        "IP disputes, contract breaches, or formal legal complaints must be escalated to legal immediately. "
        "Do not admit liability or make commitments on behalf of FSZT Partners. "
        "The CS agent should acknowledge receipt and confirm that the legal team will respond within the contracted SLA."
    ),
    "sla": (
        "Enterprise Partners: 4-hour response SLA. "
        "Growth clients: 24-hour SLA. "
        "Starter clients: 48-hour SLA. "
        "Accounts with health score below 50 are flagged for proactive CS outreach regardless of tier. "
        "VIP Enterprise accounts with open incidents are escalated to the CS team lead immediately."
    ),
    "onboarding": (
        "New Enterprise clients are assigned a Forward Deployed Engineer within 5 business days of contract signing. "
        "Growth clients are onboarded via structured sessions within 10 days. "
        "Onboarding blockers (access issues, SSO failures, missing credentials) are treated as P1 — "
        "time-to-value is the single most important metric in the first 30 days."
    ),
    "health_score": (
        "Account health scores run from 0 to 100. "
        "Below 50: high churn risk — CS team lead must be looped in for proactive retention outreach. "
        "50–70: moderate risk — monitor weekly and address any open tickets. "
        "Above 70: healthy — focus on expansion signals and QBR scheduling. "
        "Health score drops of 15+ points in a single month trigger an automatic CS review."
    ),
    "expansion": (
        "Expansion signals include: high product usage, questions about additional FSZT Labs products, "
        "new business units mentioned, upcoming renewal conversations, and unsolicited positive feedback. "
        "The CS agent should flag expansion opportunities in internal notes and route to the account's Strategist."
    ),
    "labs": (
        "FSZT Labs products (AI Sales Stack, Voice-to-Code, Pitch Agents, AI Sales Coach) follow the standard "
        "product SLA. Critical bugs blocking client workflows are P0 and require same-day escalation. "
        "The CS agent must collect a full incident brief before routing to engineering."
    ),
    "general": (
        "FSZT Partners builds and ships AI-native systems. All CS decisions must be grounded in verified "
        "client data, health scores, engagement records, and policy — never in assumptions. "
        "Every customer signal is a success opportunity. Escalate when uncertain. Ship what works."
    ),
}
