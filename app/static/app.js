"use strict";

const HINTS = {
  claude: "Uses Anthropic's `claude` CLI. Install: npm i -g @anthropic-ai/claude-code, then sign in. Optional model: sonnet / opus.",
  gemini: "Uses Google's `gemini` CLI. Install: npm i -g @google/gemini-cli, then sign in.",
  ollama: "Open-source. Install from ollama.com, then `ollama pull llama3.1`. Set a model at right.",
  openrouter: "Hosted models (DeepSeek, Qwen, …). Set OPENROUTER_API_KEY before starting. Optional model, e.g. deepseek/deepseek-chat.",
  mock: "Offline preview — reshapes your resume without a model. Great for checking the layout.",
};

let AVAILABILITY = {};
let MODELS = {};

function el(tag, cls, text) {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text != null) n.textContent = text;
  return n;
}

async function loadProviders() {
  try {
    const res = await fetch("/providers");
    const list = await res.json();
    list.forEach((p) => {
      AVAILABILITY[p.name] = p.available;
      MODELS[p.name] = p.models || [];
    });
  } catch (_) { /* non-fatal */ }
  // Default to the first detected engine so users aren't pointed at an
  // uninstalled one. Order follows the dropdown (claude, gemini, ollama,
  // openrouter, mock).
  const sel = document.getElementById("provider");
  if (!AVAILABILITY[sel.value]) {
    const firstAvail = Array.from(sel.options).find((o) => AVAILABILITY[o.value]);
    if (firstAvail) sel.value = firstAvail.value;
  }
  updateHint();
  buildModelOptions();
}

// Rebuild the model dropdown for the selected engine: a default entry, the
// engine's suggested models, and a "Custom…" escape hatch for any other id.
function buildModelOptions() {
  const provider = document.getElementById("provider").value;
  const sel = document.getElementById("model");
  sel.innerHTML = "";
  sel.appendChild(new Option("Default model", ""));
  (MODELS[provider] || []).forEach((m) => sel.appendChild(new Option(m, m)));
  sel.appendChild(new Option("Custom…", "__custom__"));
  sel.value = "";
  toggleCustom();
}

function toggleCustom() {
  const isCustom = document.getElementById("model").value === "__custom__";
  const custom = document.getElementById("model-custom");
  custom.classList.toggle("hidden", !isCustom);
  if (isCustom) custom.focus();
}

function updateHint() {
  const sel = document.getElementById("provider");
  const name = sel.value;
  const avail = AVAILABILITY[name];
  const detected = avail === undefined ? "" : avail ? " ✓ detected" : " — not detected on this machine";
  document.getElementById("provider-hint").textContent = (HINTS[name] || "") + detected;
}

function setStatus(kind, msg) {
  const s = document.getElementById("status");
  s.className = "status " + kind;
  s.textContent = msg;
}

function renderDownloads(files) {
  const wrap = document.getElementById("download-buttons");
  wrap.innerHTML = "";
  files.forEach((f) => {
    const a = el("a", null, f.label);
    a.href = f.url;
    a.setAttribute("download", "");
    wrap.appendChild(a);
  });
  document.getElementById("downloads").classList.remove("hidden");
}

function sectionTitle(parent, text) {
  parent.appendChild(el("div", "sec", text));
}

function renderResume(container, r) {
  container.innerHTML = "";
  container.appendChild(el("h3", null, r.contact.name || "—"));
  const bits = [r.contact.email, r.contact.phone, ...(r.contact.links || [])].filter(Boolean);
  container.appendChild(el("div", "contact", bits.join("   |   ")));

  if (r.summary) {
    sectionTitle(container, "Summary");
    container.appendChild(el("p", null, r.summary));
  }
  if (r.skills && r.skills.length) {
    sectionTitle(container, "Technical Skills");
    r.skills.forEach((s) => {
      const p = el("p", "skill");
      const b = el("b", null, s.label + ": ");
      p.appendChild(b);
      p.appendChild(document.createTextNode(s.items));
      container.appendChild(p);
    });
  }
  if (r.experience && r.experience.length) {
    sectionTitle(container, "Experience");
    r.experience.forEach((e) => {
      const role = el("div", "role");
      const left = e.company + (e.title ? "  —  " + e.title : "");
      role.appendChild(el("span", null, left));
      role.appendChild(el("span", "dates", e.dates || ""));
      container.appendChild(role);
      if (e.bullets && e.bullets.length) {
        const ul = el("ul");
        e.bullets.forEach((b) => ul.appendChild(el("li", null, b)));
        container.appendChild(ul);
      }
    });
  }
  if (r.education && r.education.length) {
    sectionTitle(container, "Education");
    r.education.forEach((line) => container.appendChild(el("p", null, line)));
  }
}

function renderCover(container, cl, contact) {
  container.innerHTML = "";
  container.appendChild(el("h3", null, contact.name || "—"));
  const bits = [contact.email, contact.phone, ...(contact.links || [])].filter(Boolean);
  container.appendChild(el("div", "contact", bits.join("   |   ")));
  if (cl.date) container.appendChild(el("p", null, cl.date));
  (cl.recipient || []).filter(Boolean).forEach((r) => container.appendChild(el("p", null, r)));
  if (cl.salutation) container.appendChild(el("p", null, cl.salutation));
  (cl.paragraphs || []).forEach((p) => container.appendChild(el("p", null, p)));
  if (cl.closing) container.appendChild(el("p", null, cl.closing));
  container.appendChild(el("p", null, cl.signature || contact.name || ""));
}

function switchTab(which) {
  document.querySelectorAll(".tab").forEach((t) =>
    t.classList.toggle("active", t.dataset.tab === which)
  );
  document.getElementById("preview-resume").classList.toggle("hidden", which !== "resume");
  document.getElementById("preview-cover").classList.toggle("hidden", which !== "cover");
}

async function onSubmit(ev) {
  ev.preventDefault();
  const form = ev.target;
  const btn = document.getElementById("go");
  const data = new FormData(form);
  // "Custom…" submits the free-text id instead of the sentinel option value.
  if (data.get("model") === "__custom__") {
    data.set("model", document.getElementById("model-custom").value.trim());
  }

  btn.disabled = true;
  setStatus("working", "Generating… the first run on a local model can take a minute.");
  document.getElementById("downloads").classList.add("hidden");
  document.getElementById("preview").classList.add("hidden");

  try {
    const res = await fetch("/generate", { method: "POST", body: data });
    const payload = await res.json();
    if (!res.ok) {
      setStatus("error", payload.detail || "Generation failed.");
      return;
    }
    renderDownloads(payload.files);
    renderResume(document.getElementById("preview-resume"), payload.preview.resume);
    renderCover(
      document.getElementById("preview-cover"),
      payload.preview.cover_letter,
      payload.preview.resume.contact
    );
    switchTab("resume");
    document.getElementById("preview").classList.remove("hidden");
    setStatus("done", "Done. Download your 1-page resume and cover letter below.");
  } catch (err) {
    setStatus("error", "Network error: " + err.message);
  } finally {
    btn.disabled = false;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("provider").addEventListener("change", () => {
    updateHint();
    buildModelOptions();
  });
  document.getElementById("model").addEventListener("change", toggleCustom);
  document.getElementById("tailor-form").addEventListener("submit", onSubmit);
  document.querySelectorAll(".tab").forEach((t) =>
    t.addEventListener("click", () => switchTab(t.dataset.tab))
  );
  loadProviders();
});
