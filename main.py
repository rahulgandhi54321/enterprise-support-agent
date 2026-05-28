from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
from typing import Any, Dict

import cohere
from fastapi import FastAPI
from fastapi.responses import FileResponse
from openai import OpenAI, OpenAIError

from support_operator.audit import read_recent_actions
from support_operator.agent import (
    COHERE_MODEL,
    OPENAI_FALLBACKS,
    analyze_support_request_safely,
    deterministic_triage,
)
from support_operator.models import SupportDecision, SupportRequest


app = FastAPI(title="Enterprise Support Operator", version="0.2.0")
ROOT = Path(__file__).resolve().parent


@app.get("/", response_class=FileResponse)
def console() -> FileResponse:
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/app.css", response_class=FileResponse)
def app_css() -> FileResponse:
    return FileResponse(ROOT / "static" / "app.css", media_type="text/css")


@app.get("/app.js", response_class=FileResponse)
def app_js() -> FileResponse:
    return FileResponse(ROOT / "static" / "app.js", media_type="application/javascript")


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/samples")
def samples() -> Dict[str, Any]:
    samples_path = ROOT / "data" / "sample_requests.json"
    return json.loads(samples_path.read_text(encoding="utf-8"))


@app.get("/audit/recent")
def audit_recent(limit: int = 25) -> Dict[str, Any]:
    bounded_limit = max(1, min(limit, 100))
    actions = read_recent_actions(bounded_limit)
    return {"count": len(actions), "actions": actions}


@app.get("/ops/summary")
def ops_summary() -> Dict[str, Any]:
    actions = read_recent_actions(100)
    counts: Dict[str, int] = {}
    for record in actions:
        action = str(record.get("action", "unknown"))
        counts[action] = counts.get(action, 0) + 1
    provider = os.getenv("AI_PROVIDER", "openai").lower()
    return {
        "ai_provider": provider,
        "model": COHERE_MODEL if provider == "cohere" else (OPENAI_FALLBACKS[0] if OPENAI_FALLBACKS else "gpt-4.1-mini"),
        "actions_logged": len(actions),
        "tool_counts": counts,
        "mode": "prototype",
        "approval_threshold_usd": float(os.getenv("REFUND_APPROVAL_THRESHOLD", "100")),
        "confidence_threshold": float(os.getenv("CONFIDENCE_THRESHOLD", "0.75")),
    }


@app.get("/ops/openai-diagnostics")
def openai_diagnostics() -> Dict[str, Any]:
    client = OpenAI()
    result: Dict[str, Any] = {
        "provider": "openai",
        "auth": "unknown",
        "models_list": "not_run",
        "generation": "not_run",
        "likely_cause": "",
        "next_steps": [],
    }
    try:
        models = client.models.list()
        result["auth"] = "ok"
        result["models_list"] = "ok"
        result["sample_models"] = [m.id for m in models.data[:8]]
    except OpenAIError as exc:
        result["auth"] = "failed"
        result["models_list"] = exc.__class__.__name__
        result["likely_cause"] = "The API key or project cannot authenticate against OpenAI."
        result["next_steps"] = [
            "Create a new OpenAI project API key.",
            "Confirm the key is saved in .env.local as OPENAI_API_KEY.",
        ]
        return result

    try:
        response = client.responses.create(
            model=OPENAI_FALLBACKS[0] if OPENAI_FALLBACKS else "gpt-4.1-mini",
            instructions="Return exactly ok",
            input="ping",
            max_output_tokens=16,
        )
        result["generation"] = "ok"
        result["generation_text"] = getattr(response, "output_text", "")
        result["usage"] = response.usage.model_dump() if getattr(response, "usage", None) else {}
    except OpenAIError as exc:
        result["generation"] = exc.__class__.__name__
        result["generation_error"] = str(exc)[:500]
        result["likely_cause"] = "Auth works but generation failed. Check billing or spend limits."
        result["next_steps"] = [
            "Confirm API billing/credits are active at platform.openai.com.",
            "Try the same key in the OpenAI Playground with a tiny prompt.",
        ]

    return result


@app.get("/ops/cohere-diagnostics")
async def cohere_diagnostics() -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "provider": "cohere",
        "auth": "unknown",
        "generation": "not_run",
        "model": COHERE_MODEL,
        "likely_cause": "",
        "next_steps": [],
    }
    client = cohere.AsyncClientV2(api_key=os.getenv("COHERE_API_KEY", ""))
    try:
        response = await client.chat(
            model=COHERE_MODEL,
            messages=[{"role": "user", "content": "Return exactly: ok"}],
        )
        result["auth"] = "ok"
        result["generation"] = "ok"
        result["generation_text"] = response.message.content[0].text if response.message.content else ""
        result["usage"] = {
            "input_tokens": int(getattr(response.usage.tokens, "input_tokens", 0) or 0),
            "output_tokens": int(getattr(response.usage.tokens, "output_tokens", 0) or 0),
        }
    except cohere.errors.unauthorized_error.UnauthorizedError:
        result["auth"] = "failed"
        result["generation"] = "UnauthorizedError"
        result["likely_cause"] = "COHERE_API_KEY is missing or invalid."
        result["next_steps"] = [
            "Add COHERE_API_KEY to .env.local.",
            "Get a key at dashboard.cohere.com.",
        ]
    except Exception as exc:
        result["auth"] = "unknown"
        result["generation"] = exc.__class__.__name__
        result["generation_error"] = str(exc)[:500]
        result["likely_cause"] = "Cohere API call failed."
        result["next_steps"] = ["Check COHERE_API_KEY in .env.local.", "Check dashboard.cohere.com for account status."]

    return result


@app.post("/analyze", response_model=SupportDecision)
async def analyze(request: SupportRequest) -> SupportDecision:
    return await analyze_support_request_safely(request)


@app.post("/triage-demo")
def triage_demo(request: SupportRequest) -> Dict[str, Any]:
    return deterministic_triage(request)


def _load_sample(name: str) -> SupportRequest:
    samples_path = ROOT / "data" / "sample_requests.json"
    samples = json.loads(samples_path.read_text(encoding="utf-8"))
    if name not in samples:
        raise SystemExit(f"Unknown sample '{name}'. Available: {', '.join(sorted(samples))}")
    return SupportRequest.model_validate(samples[name])


async def _run_cli(sample: str, live: bool) -> None:
    request = _load_sample(sample)
    if live:
        decision = await analyze_support_request_safely(request)
        print(decision.model_dump_json(indent=2))
    else:
        print(json.dumps(deterministic_triage(request), indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Enterprise customer support operator prototype")
    parser.add_argument("--sample", default=None, help="Run a sample request from data/sample_requests.json")
    parser.add_argument("--live", action="store_true", help="Use the live AI path (OpenAI or Claude based on AI_PROVIDER)")
    parser.add_argument("--host", default=os.getenv("HOST", "0.0.0.0" if os.getenv("PORT") else "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", "8000")))
    args = parser.parse_args()

    if args.sample:
        asyncio.run(_run_cli(args.sample, args.live))
        return

    import uvicorn
    uvicorn.run("main:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
