/* ─── FSZT AI Customer Success Agent — UI Logic ────────────── */

/* ─── LinkedIn deep link ─────────────────────────────────── */
function openLinkedIn(e) {
  e.preventDefault();
  // Try to open the LinkedIn app first
  window.location.href = 'linkedin://in/rahul-gandhi-72b9181a7';
  // Fall back to web profile after 600ms if app didn't intercept
  setTimeout(() => {
    window.open('https://www.linkedin.com/in/rahul-gandhi-72b9181a7/', '_blank');
  }, 600);
}

const RING_CIRCUMFERENCE = 226.19;

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

let backendSamples = {};

/* ─── Helpers ────────────────────────────────────────────── */
const $ = (id) => document.getElementById(id);
const setText = (id, val) => { const el = $(id); if (el) el.textContent = val; };
const pretty = (v) => (!v || (typeof v === "object" && !Object.keys(v).length)) ? "{}" : JSON.stringify(v, null, 2);
const boolText = (v) => v ? "Yes" : "No";

/* ─── SVG gradient injection ─────────────────────────────── */
function injectSvgDefs() {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("width", "0");
  svg.setAttribute("height", "0");
  svg.style.position = "absolute";
  svg.innerHTML = `
    <defs>
      <linearGradient id="ringGradient" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#4f46e5"/>
        <stop offset="100%" stop-color="#7c3aed"/>
      </linearGradient>
    </defs>`;
  document.body.prepend(svg);
}

/* ─── Confidence ring ────────────────────────────────────── */
function setConfidence(score) {
  const pct = Math.round(score * 100);
  const offset = RING_CIRCUMFERENCE - (score * RING_CIRCUMFERENCE);
  const ring = $("confidenceRing");
  if (ring) ring.style.strokeDashoffset = offset;
  animateNumber("confidenceValue", pct, "%");
}

function animateNumber(id, target, suffix = "") {
  const el = $(id);
  if (!el) return;
  const start = parseInt(el.textContent) || 0;
  const duration = 700;
  const startTime = performance.now();
  const ease = (t) => t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
  const step = (now) => {
    const elapsed = now - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const val = Math.round(start + (target - start) * ease(progress));
    el.textContent = val + suffix;
    if (progress < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

/* ─── Badge styling ──────────────────────────────────────── */
const PRIORITY_CLASS = {
  "urgent": "badge-urgent",
  "high":   "badge-high",
  "medium": "badge-medium",
  "low":    "badge-low",
};

const PRIORITY_ICON = {
  "urgent": "🚨",
  "high":   "⚠️",
  "medium": "●",
  "low":    "↓",
};

const SENTIMENT_CLASS = {
  "angry":      "badge-danger",
  "distressed": "badge-warning",
  "negative":   "badge-warning",
  "neutral":    "badge-neutral",
  "positive":   "badge-success",
};

const SENTIMENT_ICON = {
  "angry":      "😤",
  "distressed": "😟",
  "negative":   "😞",
  "neutral":    "😐",
  "positive":   "😊",
};

const ESCALATION_CLASS = {
  "not escalated":                   "badge-low",
  "human review required":           "badge-warning",
  "security escalation required":    "badge-danger",
  "legal escalation required":       "badge-urgent",
  "approval required":               "badge-violet",
};

const ESCALATION_ICON = {
  "not escalated":                   "✓",
  "human review required":           "👤",
  "security escalation required":    "🛡️",
  "legal escalation required":       "⚖️",
  "approval required":               "🔒",
};

function setBadge(id, text, classMap, iconMap) {
  const el = $(id);
  if (!el) return;
  const key = (text || "").toLowerCase();
  const cls = classMap[key] || "badge-neutral";
  const icon = iconMap[key] || "";
  el.className = `status-badge ${cls}`;
  el.textContent = (icon ? icon + " " : "") + (text || "—");
}

/* ─── Risk cells ─────────────────────────────────────────── */
function setRisk(cellId, valId, isRisk, text) {
  const cell = $(cellId);
  const val = $(valId);
  if (!cell || !val) return;
  cell.className = "risk-cell " + (isRisk ? "risk-yes" : "risk-no");
  val.textContent = text || boolText(isRisk);
}

/* ─── System dots ────────────────────────────────────────── */
function setSysDot(dotId, active) {
  const el = $(dotId);
  if (el) el.className = "sys-dot" + (active ? " active" : "");
}

/* ─── Tool timeline ──────────────────────────────────────── */
function renderToolTimeline(actions) {
  const list = $("toolActions");
  if (!list) return;
  list.innerHTML = "";
  if (!actions || !actions.length) {
    list.innerHTML = '<li class="tl-empty">No tool actions recorded.</li>';
    return;
  }
  actions.forEach((a) => {
    const ok = a.status === "success";
    const li = document.createElement("li");
    li.className = "tl-item";
    li.innerHTML = `
      <div class="tl-dot ${ok ? "" : "failed"}">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round">
          ${ok
            ? '<polyline points="20 6 9 17 4 12"/>'
            : '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>'}
        </svg>
      </div>
      <div class="tl-body">
        <div class="tl-tool">${a.tool}</div>
        <div class="tl-purpose">${a.purpose}</div>
        <div class="tl-detail">${a.detail}</div>
      </div>`;
    list.appendChild(li);
  });
}

/* ─── Audit feed ─────────────────────────────────────────── */
function renderAuditFeed(actions) {
  const list = $("auditEvents");
  if (!list) return;
  list.innerHTML = "";
  if (!actions || !actions.length) {
    list.innerHTML = '<li class="tl-empty">No audit events yet.</li>';
    return;
  }
  actions.slice().reverse().slice(0, 8).forEach((e) => {
    const li = document.createElement("li");
    const purpose = e.payload?.purpose || "Action logged";
    const status = e.payload?.status || "recorded";
    li.innerHTML = `<strong>${e.action}</strong><span style="color:var(--muted);font-size:11px">${purpose} · ${status}</span>`;
    list.appendChild(li);
  });
}

/* ─── Runtime logs ───────────────────────────────────────── */
function renderRuntimeLogs(logs) {
  const list = $("runtimeLogs");
  if (!list) return;
  list.innerHTML = "";
  if (!logs || !logs.length) {
    list.innerHTML = '<li>No runtime logs yet.</li>';
    return;
  }
  logs.forEach((line) => {
    const li = document.createElement("li");
    li.textContent = line;
    list.appendChild(li);
  });
}

/* ─── Main render ────────────────────────────────────────── */
function renderDecision(data) {
  setText("decisionTitle", data.ticket_category || "Decision ready");

  // Confidence ring
  setConfidence(data.confidence_score || 0);

  // Category badge
  const catBadge = $("categoryBadge");
  if (catBadge) {
    catBadge.style.display = "inline-flex";
    catBadge.textContent = data.ticket_category || "";
    catBadge.className = "chip chip-outline";
  }

  // Status badges
  setBadge("badgePriority", data.priority, PRIORITY_CLASS, PRIORITY_ICON);
  setBadge("badgeSentiment", data.sentiment, SENTIMENT_CLASS, SENTIMENT_ICON);
  setBadge("badgeEscalation", data.escalation_status, ESCALATION_CLASS, ESCALATION_ICON);

  // Text fields
  setText("suggestedAction", data.suggested_action || "—");
  setText("draftReply", data.draft_reply || "—");
  setText("internalNotes", data.internal_notes || "No internal notes.");

  // Risk cells
  setRisk("riskSla", "slaRisk", data.sla_risk, data.sla_risk ? "Yes ⚠️" : "No");
  setRisk("riskChurn", "churnRisk", data.churn_risk, data.churn_risk ? "Yes ⚠️" : "No");
  setRisk("riskVip", "vipCustomer", data.vip_customer, data.vip_customer ? "Yes 👑" : "No");
  const hasFraud = data.fraud_or_spam_indicators?.length > 0;
  setRisk("riskFraud", "fraudFlags", hasFraud, hasFraud ? data.fraud_or_spam_indicators.join(", ") : "None");

  // System dots
  const hasCrm = data.customer_context && Object.keys(data.customer_context).length > 0;
  const hasOrder = data.order_context && Object.keys(data.order_context).length > 0;
  const hasPolicy = data.policy_context && Object.keys(data.policy_context).length > 0;
  setSysDot("dotCrm", hasCrm);
  setSysDot("dotOrder", hasOrder);
  setSysDot("dotPolicy", hasPolicy);
  setSysDot("dotAudit", true);
  setText("crmSystem", hasCrm ? "Account loaded" : "No profile");
  setText("orderSystem", hasOrder ? "Engagement verified" : "No record");
  setText("policySystem", hasPolicy ? "Playbook matched" : "General playbook");
  setText("auditSystem", data.audit_summary || "Logged");

  // Context pres
  setText("customerContext", pretty(data.customer_context));
  setText("orderContext", pretty(data.order_context));
  setText("policyContext", pretty(data.policy_context));

  // Tool timeline
  renderToolTimeline(data.tool_actions_performed);

  // Telemetry
  setText("aiStatus", data.ai_status || "—");
  setText("modelUsed", data.model_used || "—");
  setText("latencyMs", data.latency_ms ? data.latency_ms + " ms" : "—");
  setText("totalTokens", data.api_usage?.total_tokens ?? data.api_usage?.output_tokens ?? "—");
  setText("apiUsage", pretty(data.api_usage));
  renderRuntimeLogs(data.runtime_logs);

  // Ops refresh
  refreshOps();

  // On mobile, auto-switch to results pane
  if (window.innerWidth <= 768) {
    switchPane("decision");
  }
}

function renderError(message) {
  setText("decisionTitle", "Request failed");
  setText("suggestedAction", "Check that the server is running, then try again.");
  const reply = $("draftReply");
  if (reply) { reply.textContent = message; reply.classList.add("error-text"); }
}

/* ─── Health check ───────────────────────────────────────── */
async function checkHealth() {
  const pill = $("healthPill");
  const status = $("healthStatus");
  try {
    const res = await fetch("/health");
    if (!res.ok) throw new Error();
    if (pill) pill.className = "health-pill ok";
    if (status) status.textContent = "Online";
  } catch {
    if (pill) pill.className = "health-pill fail";
    if (status) status.textContent = "Offline";
  }
}

/* ─── Ops summary ────────────────────────────────────────── */
async function refreshOps() {
  try {
    const [summaryRes, auditRes] = await Promise.all([
      fetch("/ops/summary"),
      fetch("/audit/recent?limit=8"),
    ]);
    const summary = await summaryRes.json();
    const audit = await auditRes.json();
    setText("opsSummary", pretty(summary));
    renderAuditFeed(audit.actions);
  } catch {
    setText("opsSummary", "{}");
  }
}

/* ─── Load backend samples ───────────────────────────────── */
async function loadSamples() {
  const sel = $("backendSamples");
  try {
    const res = await fetch("/samples");
    backendSamples = await res.json();
    Object.entries(backendSamples).forEach(([key, sample]) => {
      const opt = document.createElement("option");
      opt.value = key;
      opt.textContent = key.replaceAll("_", " ");
      sel.appendChild(opt);
    });
  } catch {
    if (sel) sel.disabled = true;
  }
}

/* ─── Loading state ──────────────────────────────────────── */
function setLoading(on) {
  const btn = $("analyzeButton");
  const label = $("submitLabel");
  if (!btn || !label) return;
  btn.disabled = on;
  label.textContent = on ? "Running AI agent…" : "Run AI agent";
  if (on) {
    setText("decisionTitle", "AI agent working…");
    const ring = $("confidenceRing");
    if (ring) ring.style.strokeDashoffset = RING_CIRCUMFERENCE;
    const reply = $("draftReply");
    if (reply) reply.classList.remove("error-text");
  }
}

/* ─── Diagnostics ────────────────────────────────────────── */
async function runDiagnostics(endpoint, buttonId) {
  const btn = $(buttonId);
  const orig = btn.textContent;
  btn.disabled = true;
  btn.textContent = "Checking…";
  setText("aiDiagnostics", `Running ${endpoint} diagnostics…`);
  try {
    const res = await fetch(`/ops/${endpoint}-diagnostics`);
    const data = await res.json();
    setText("aiDiagnostics", pretty(data));
  } catch (e) {
    setText("aiDiagnostics", `Failed: ${e.message}`);
  } finally {
    btn.disabled = false;
    btn.textContent = orig;
  }
}

/* ─── Mobile tab switching ───────────────────────────────── */
function switchPane(name) {
  // Only do tab switching on mobile — on desktop both panes are always visible
  if (window.innerWidth > 768) return;
  document.querySelectorAll(".pane").forEach((p) => p.classList.remove("pane-active"));
  document.querySelectorAll(".mobile-tab").forEach((t) => t.classList.remove("active"));
  const pane = name === "request" ? $("paneRequest") : $("paneDecision");
  const tab  = name === "request" ? $("tabRequest")  : $("tabDecision");
  if (pane) { pane.classList.add("pane-active"); pane.scrollTop = 0; }
  if (tab)  tab.classList.add("active");
}

/* ─── Settings panel ─────────────────────────────────────── */
function toggleSettings() {
  const panel    = $("settingsPanel");
  const backdrop = $("settingsBackdrop");
  const btn      = $("settingsButton");
  if (!panel) return;

  const opening = panel.hidden;
  panel.hidden    = !opening;
  backdrop.hidden = !opening;
  btn.classList.toggle("active", opening);
  btn.setAttribute("aria-expanded", String(opening));

  // Prevent body scroll while sheet is open on mobile
  document.body.style.overflow = (opening && window.innerWidth <= 768) ? "hidden" : "";
}

function closeSettings() {
  const panel = $("settingsPanel");
  if (panel && !panel.hidden) toggleSettings();
}

/* ─── Event wiring ───────────────────────────────────────── */

// Sample chips
document.querySelectorAll("[data-sample]").forEach((btn) => {
  btn.addEventListener("click", () => {
    const key = btn.dataset.sample;
    const s = samples[key];
    if (!s) return;
    const ch = $("channel"); if (ch) ch.value = s.channel;
    const cu = $("customerId"); if (cu) cu.value = s.customer_id;
    const mg = $("message"); if (mg) mg.value = s.message;
  });
});

// Backend samples dropdown
const backendSel = $("backendSamples");
if (backendSel) {
  backendSel.addEventListener("change", (e) => {
    const s = backendSamples[e.target.value];
    if (!s) return;
    const ch = $("channel"); if (ch) ch.value = s.channel;
    const cu = $("customerId"); if (cu) cu.value = s.customer_id || "";
    const mg = $("message"); if (mg) mg.value = s.message;
  });
}

// Settings open/close
const settingsBtn = $("settingsButton");
if (settingsBtn) settingsBtn.addEventListener("click", toggleSettings);
const closeBtn = $("closeSettings");
if (closeBtn) closeBtn.addEventListener("click", closeSettings);

// Backdrop tap closes panel
$("settingsBackdrop")?.addEventListener("click", closeSettings);

// Desktop: close on outside click (backdrop handles mobile)
document.addEventListener("click", (e) => {
  const panel = $("settingsPanel");
  const btn   = $("settingsButton");
  const backdrop = $("settingsBackdrop");
  if (
    panel && !panel.hidden &&
    !panel.contains(e.target) &&
    !btn.contains(e.target) &&
    !backdrop?.contains(e.target) &&
    window.innerWidth > 768
  ) {
    closeSettings();
  }
});

// Escape key closes panel
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeSettings();
});

// Diagnostics
$("runOpenaiDiagnostics")?.addEventListener("click", () => runDiagnostics("openai", "runOpenaiDiagnostics"));
$("runCohereDiagnostics")?.addEventListener("click", () => runDiagnostics("cohere", "runCohereDiagnostics"));

// Jump to results (mobile)
$("jumpToResults")?.addEventListener("click", () => {
  if (window.innerWidth <= 768) {
    switchPane("decision");
  } else {
    $("paneDecision")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }
});

// Mobile tabs
$("tabRequest")?.addEventListener("click", () => switchPane("request"));
$("tabDecision")?.addEventListener("click", () => switchPane("decision"));

// Form submit
const form = document.querySelector("#supportForm");
if (form) {
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const mode = new FormData(form).get("mode");
    const payload = {
      channel: $("channel")?.value,
      customer_id: $("customerId")?.value || null,
      message: $("message")?.value,
    };

    setLoading(true);
    renderRuntimeLogs(["Signal received.", mode === "analyze" ? "Calling live AI agent route." : "Running demo mode — no AI calls."]);

    try {
      const res = await fetch(`/${mode}`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Analysis failed");
      renderDecision(data);
    } catch (err) {
      renderError(err.message);
    } finally {
      setLoading(false);
    }
  });
}

/* ─── Init ───────────────────────────────────────────────── */

// Initialise the correct tab state on mobile
function initPanes() {
  if (window.innerWidth <= 768) {
    // Make sure request pane and tab are both active
    document.querySelectorAll(".mobile-tab").forEach((t) => t.classList.remove("active"));
    const tabReq = $("tabRequest");
    if (tabReq) tabReq.classList.add("active");
    // paneRequest already has pane-active in HTML; just make sure decision doesn't
    const dec = $("paneDecision");
    if (dec) dec.classList.remove("pane-active");
  }
}
initPanes();

injectSvgDefs();
checkHealth();
loadSamples();
refreshOps();
