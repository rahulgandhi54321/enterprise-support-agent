const samples = {
  billing: {
    channel: "email",
    customer_id: "cli_enterprise_001",
    message: "We received two invoices for engagement ORD-1001 this month and nobody has responded. Fix this today or we are escalating to legal and terminating the contract.",
  },
  technical: {
    channel: "chat",
    customer_id: "cli_growth_002",
    message: "The AI-First Call Center agent your team deployed is throwing a 500 error on every inbound call routing request. Our contact centre is completely blocked.",
  },
  access: {
    channel: "whatsapp",
    customer_id: "cli_starter_003",
    message: "I lost access to the AI Native Consultants course portal after our company switched SSO providers. Our cohort starts tomorrow — I need this restored urgently.",
  },
  legal: {
    channel: "support_portal",
    customer_id: "cli_enterprise_001",
    message: "This is a formal legal complaint. The Discovery Agent your team deployed exposed client PII in its outputs last night. We need your legal and security teams to respond within the hour.",
  },
};

const form = document.querySelector("#supportForm");
const button = document.querySelector("#analyzeButton");
let backendSamples = {};

function setText(id, value) {
  document.querySelector(`#${id}`).textContent = value;
}

function boolText(value) {
  return value ? "Yes" : "No";
}

function pretty(value) {
  if (!value || (typeof value === "object" && Object.keys(value).length === 0)) {
    return "{}";
  }
  return JSON.stringify(value, null, 2);
}

function setClassByValue(elementId, value, prefix) {
  const element = document.querySelector(`#${elementId}`);
  element.className = "";
  if (!value) return;
  element.classList.add(`${prefix}-${String(value).toLowerCase().replaceAll(" ", "-")}`);
}

function renderDecision(data) {
  setText("decisionTitle", data.ticket_category || "Decision ready");
  setText("confidenceValue", `${Math.round((data.confidence_score || 0) * 100)}%`);
  setText("category", data.ticket_category || "-");
  setText("priority", data.priority || "-");
  setText("sentiment", data.sentiment || "-");
  setText("escalation", data.escalation_status || "-");
  setText("suggestedAction", data.suggested_action || "-");
  setText("draftReply", data.draft_reply || "-");
  setText("slaRisk", boolText(data.sla_risk));
  setText("churnRisk", boolText(data.churn_risk));
  setText("vipCustomer", boolText(data.vip_customer));
  setText("fraudFlags", (data.fraud_or_spam_indicators || []).join(", ") || "None");
  setText("internalNotes", data.internal_notes || "-");
  setText("customerContext", pretty(data.customer_context));
  setText("orderContext", pretty(data.order_context));
  setText("policyContext", pretty(data.policy_context));
  setText("auditSystem", data.audit_summary || "Logged");
  setText("crmSystem", data.customer_context && Object.keys(data.customer_context).length ? "Profile loaded" : "No profile");
  setText("orderSystem", data.order_context && Object.keys(data.order_context).length ? "Order verified" : "No order");
  setText("policySystem", data.policy_context && Object.keys(data.policy_context).length ? "Policy matched" : "General SOP");
  setText("aiStatus", data.ai_status || "unknown");
  setText("modelUsed", data.model_used || "demo");
  setText("latencyMs", data.latency_ms ? `${data.latency_ms} ms` : "-");
  setText("apiUsage", pretty(data.api_usage));
  setText("totalTokens", data.api_usage && data.api_usage.total_tokens ? data.api_usage.total_tokens : "-");
  renderRuntimeLogs(data.runtime_logs || []);

  setClassByValue("priority", data.priority, "priority");
  document.querySelector("#escalation").className =
    data.escalation_status && data.escalation_status !== "Not escalated" ? "escalated" : "clear";
  document.querySelector("#slaRisk").className = data.sla_risk ? "risk-yes" : "risk-no";
  document.querySelector("#churnRisk").className = data.churn_risk ? "risk-yes" : "risk-no";
  document.querySelector("#vipCustomer").className = data.vip_customer ? "risk-yes" : "risk-no";

  const toolList = document.querySelector("#toolActions");
  toolList.innerHTML = "";
  const actions = data.tool_actions_performed || [];
  if (!actions.length) {
    const item = document.createElement("li");
    item.textContent = "No tool actions were reported for this run.";
    toolList.appendChild(item);
    return;
  }
  actions.forEach((action) => {
    const item = document.createElement("li");
    item.innerHTML = `<strong>${action.tool}</strong><br>${action.purpose}<br>${action.status} - ${action.detail}`;
    toolList.appendChild(item);
  });
  refreshOps();
}

function renderRuntimeLogs(logs) {
  const runtimeList = document.querySelector("#runtimeLogs");
  runtimeList.innerHTML = "";
  if (!logs.length) {
    const item = document.createElement("li");
    item.textContent = "No runtime logs yet.";
    runtimeList.appendChild(item);
    return;
  }
  logs.forEach((line) => {
    const item = document.createElement("li");
    item.textContent = line;
    runtimeList.appendChild(item);
  });
}

function renderError(message) {
  setText("decisionTitle", "Request failed");
  setText("suggestedAction", "Check that the server is running, then try again.");
  setText("draftReply", message);
  document.querySelector("#draftReply").classList.add("error");
}

async function checkHealth() {
  const status = document.querySelector("#healthStatus");
  try {
    const response = await fetch("/health");
    if (!response.ok) throw new Error("Health check failed");
    status.textContent = "API online";
    status.className = "status ok";
  } catch {
    status.textContent = "API offline";
    status.className = "status fail";
  }
}

async function loadSamples() {
  const sampleSelect = document.querySelector("#backendSamples");
  try {
    const response = await fetch("/samples");
    backendSamples = await response.json();
    Object.entries(backendSamples).forEach(([key, sample]) => {
      const option = document.createElement("option");
      option.value = key;
      option.textContent = key.replaceAll("_", " ");
      option.dataset.channel = sample.channel;
      sampleSelect.appendChild(option);
    });
  } catch {
    sampleSelect.disabled = true;
  }
}

async function refreshOps() {
  try {
    const [summaryResponse, auditResponse] = await Promise.all([
      fetch("/ops/summary"),
      fetch("/audit/recent?limit=8"),
    ]);
    const summary = await summaryResponse.json();
    const audit = await auditResponse.json();
    setText("opsSummary", pretty(summary));

    const auditList = document.querySelector("#auditEvents");
    auditList.innerHTML = "";
    if (!audit.actions || !audit.actions.length) {
      const item = document.createElement("li");
      item.textContent = "No audit events yet.";
      auditList.appendChild(item);
      return;
    }
    audit.actions.slice().reverse().forEach((event) => {
      const item = document.createElement("li");
      const purpose = event.payload && event.payload.purpose ? event.payload.purpose : "Action logged";
      const status = event.payload && event.payload.status ? event.payload.status : "recorded";
      item.innerHTML = `<strong>${event.action}</strong><br>${purpose}<br>${status}`;
      auditList.appendChild(item);
    });
  } catch {
    setText("opsSummary", "{}");
  }
}

document.querySelectorAll("[data-sample]").forEach((sampleButton) => {
  sampleButton.addEventListener("click", () => {
    const key = sampleButton.dataset.sample;
    const sample = samples[key];
    if (!sample) return;
    document.querySelector("#channel").value = sample.channel;
    document.querySelector("#customerId").value = sample.customer_id;
    document.querySelector("#message").value = sample.message;
  });
});

document.querySelector("#backendSamples").addEventListener("change", (event) => {
  const sample = backendSamples[event.target.value];
  if (!sample) return;
  document.querySelector("#channel").value = sample.channel;
  document.querySelector("#customerId").value = sample.customer_id || "";
  document.querySelector("#message").value = sample.message;
});

document.querySelector("#settingsButton").addEventListener("click", () => {
  const panel = document.querySelector("#settingsPanel");
  const button = document.querySelector("#settingsButton");
  const isOpen = !panel.hidden;
  panel.hidden = isOpen;
  button.setAttribute("aria-expanded", String(!isOpen));
});

document.querySelector("#closeSettings").addEventListener("click", () => {
  document.querySelector("#settingsPanel").hidden = true;
  document.querySelector("#settingsButton").setAttribute("aria-expanded", "false");
});

async function runDiagnostics(endpoint, buttonId) {
  const button = document.querySelector(`#${buttonId}`);
  const original = button.textContent;
  button.disabled = true;
  button.textContent = "Checking…";
  setText("aiDiagnostics", `Running ${endpoint} diagnostics…`);
  try {
    const response = await fetch(`/ops/${endpoint}-diagnostics`);
    const data = await response.json();
    setText("aiDiagnostics", pretty(data));
  } catch (error) {
    setText("aiDiagnostics", `Diagnostics failed: ${error.message}`);
  } finally {
    button.disabled = false;
    button.textContent = original;
  }
}

document.querySelector("#runOpenaiDiagnostics").addEventListener("click", () => runDiagnostics("openai", "runOpenaiDiagnostics"));
document.querySelector("#runCohereDiagnostics").addEventListener("click", () => runDiagnostics("cohere", "runCohereDiagnostics"));

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  document.querySelector("#draftReply").classList.remove("error");
  const mode = new FormData(form).get("mode");
  const payload = {
    channel: document.querySelector("#channel").value,
    customer_id: document.querySelector("#customerId").value || null,
    message: document.querySelector("#message").value,
  };

  button.disabled = true;
  button.textContent = mode === "analyze" ? "Running live AI" : "Analyzing";
  setText("decisionTitle", "Analyzing request");
  setText("aiStatus", mode === "analyze" ? "live_ai_running" : "demo_running");
  renderRuntimeLogs(["Request submitted.", mode === "analyze" ? "Calling live AI route." : "Running deterministic demo tools."]);

  try {
    const response = await fetch(`/${mode}`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Analysis failed");
    renderDecision(data);
  } catch (error) {
    renderError(error.message);
  } finally {
    button.disabled = false;
    button.textContent = "Analyze request";
  }
});

document.querySelector("#jumpToResults").addEventListener("click", () => {
  document.querySelector(".decision-pane").scrollIntoView({ behavior: "smooth", block: "start" });
});

checkHealth();
loadSamples();
refreshOps();
