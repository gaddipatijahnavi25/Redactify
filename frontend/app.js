/* ── PIIGuard App ───────────────────────────────────────────────────────── */
const API = window.location.origin + "/api";

const ALL_CATS = [
    "EMAIL", "PHONE_IN", "PHONE_INTL", "AADHAAR", "PAN", "SSN",
    "PASSPORT", "CREDIT_CARD", "IFSC", "IP_V4", "DOB", "URL",
    "PERSON", "GPE", "LOC", "ORG", "DATE", "NORP"
];
const STYLE_HINTS = {
    label: "Replaces with [ENTITY_TYPE]",
    stars: "Replaces every character with *",
    partial: "Keeps first/last character: J***e",
};

// ── DOM ───────────────────────────────────────────────────────────────────
const $ = id => document.getElementById(id);
const dropzone = $("dropzone"), fileInput = $("fileInput");
const fileBar = $("fileBar"), fileExt = $("fileExt");
const fileName = $("fileName"), fileSize = $("fileSize");
const clearBtn = $("clearBtn"), redactBtn = $("redactBtn");
const btnLabel = $("btnLabel"), spinner = $("spinner");
const textInput = $("textInput"), redactTextBtn = $("redactTextBtn");
const textBtnLbl = $("textBtnLabel"), textSpinner = $("textSpinner");
const scanOnly = $("scanOnly"), thrSlider = $("thrSlider"), thrVal = $("thrVal");
const styleHint = $("styleHint"), catGrid = $("catGrid");
const errorBar = $("errorBar"), errorMsg = $("errorMsg");
const results = $("results"), resMeta = $("resMeta"), resTitle = $("resTitle");
const resActions = $("resActions"), statGrid = $("statGrid");
const diffCard = $("diffCard"), diffBody = $("diffBody");
const copyBtn = $("copyBtn"), piiBody = $("piiBody");
const tblBadge = $("tblBadge"), bkBars = $("bkBars");
const histList = $("histList");

// ── State ─────────────────────────────────────────────────────────────────
let file = null, activeStyle = "label", activeMode = "file", lastRedacted = "";

const fmt = b => b < 1024 ? b + "B" : b < 1 << 20 ? (b / 1024).toFixed(1) + "KB" : (b / (1 << 20)).toFixed(1) + "MB";
const esc = s => String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

// ── Init categories ───────────────────────────────────────────────────────
ALL_CATS.forEach(c => {
    catGrid.insertAdjacentHTML("beforeend",
        `<input type="checkbox" class="cat-check" id="cat_${c}" value="${c}" checked /><label class="cat-label" for="cat_${c}">${c}</label>`);
});

// ── Tab switch ────────────────────────────────────────────────────────────
window.switchTab = name => {
    activeMode = name;
    $("tabFile").classList.toggle("active", name === "file");
    $("tabText").classList.toggle("active", name === "text");
    $("fileMode").classList.toggle("hidden", name !== "file");
    $("textMode").classList.toggle("hidden", name !== "text");
    results.classList.add("hidden");
    errorBar.classList.add("hidden");
};

// ── Style pills ───────────────────────────────────────────────────────────
window.setStyle = btn => {
    document.querySelectorAll(".pill").forEach(p => p.classList.remove("active"));
    btn.classList.add("active");
    activeStyle = btn.dataset.style;
    styleHint.textContent = STYLE_HINTS[activeStyle];
};

// ── Threshold slider ──────────────────────────────────────────────────────
thrSlider.addEventListener("input", () => { thrVal.textContent = thrSlider.value + "%"; });

// ── Helpers ───────────────────────────────────────────────────────────────
const getThreshold = () => parseInt(thrSlider.value) / 100;
const getScanOnly = () => scanOnly.checked;
const getCategories = () => {
    const checked = [...document.querySelectorAll(".cat-check:checked")].map(el => el.value);
    return checked.length === ALL_CATS.length ? "" : checked.join(",");
};

// ── Drag & drop ───────────────────────────────────────────────────────────
dropzone.addEventListener("dragover", e => { e.preventDefault(); dropzone.classList.add("over"); });
dropzone.addEventListener("dragleave", () => dropzone.classList.remove("over"));
dropzone.addEventListener("drop", e => { e.preventDefault(); dropzone.classList.remove("over"); const f = e.dataTransfer.files[0]; if (f) pick(f); });
dropzone.addEventListener("click", e => { if (!e.target.classList.contains("link")) fileInput.click(); });
fileInput.addEventListener("change", () => fileInput.files[0] && pick(fileInput.files[0]));

function pick(f) {
    file = f;
    fileExt.textContent = f.name.split(".").pop().toUpperCase().slice(0, 4);
    fileName.textContent = f.name;
    fileSize.textContent = fmt(f.size);
    fileBar.classList.remove("hidden");
    redactBtn.disabled = false;
    results.classList.add("hidden");
    errorBar.classList.add("hidden");
}

clearBtn.addEventListener("click", () => {
    file = null; fileInput.value = "";
    fileBar.classList.add("hidden");
    redactBtn.disabled = true;
    results.classList.add("hidden");
    errorBar.classList.add("hidden");
});

$("clearTextBtn").addEventListener("click", () => {
    textInput.value = "";
    results.classList.add("hidden");
    errorBar.classList.add("hidden");
});

// ── File redact ───────────────────────────────────────────────────────────
redactBtn.addEventListener("click", async () => {
    if (!file) return;
    setLoad(true, btnLabel, spinner);
    results.classList.add("hidden"); errorBar.classList.add("hidden");
    try {
        const form = new FormData();
        form.append("file", file);
        form.append("style", activeStyle);
        form.append("threshold", getThreshold());
        form.append("categories", getCategories());
        form.append("scan_only", getScanOnly());
        const res = await fetch(`${API}/redact`, { method: "POST", body: form });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Server error");
        render(data);
        addHistory({ name: file.name, type: data.file_type, total: data.report?.pii_summary?.total_detected ?? 0 });
    } catch (e) { showError(e.message); }
    finally { setLoad(false, btnLabel, spinner, "Detect & Redact PII"); }
});

// ── Text redact ───────────────────────────────────────────────────────────
redactTextBtn.addEventListener("click", async () => {
    const txt = textInput.value.trim();
    if (!txt) return;
    setLoad(true, textBtnLbl, textSpinner);
    results.classList.add("hidden"); errorBar.classList.add("hidden");
    try {
        const cats = getCategories().split(",").filter(Boolean);
        const res = await fetch(`${API}/redact-text`, {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: txt, style: activeStyle, threshold: getThreshold(), categories: cats, scan_only: getScanOnly() }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Server error");
        render(data);
        addHistory({ name: "<text input>", type: "text", total: data.report?.pii_summary?.total_detected ?? 0 });
    } catch (e) { showError(e.message); }
    finally { setLoad(false, textBtnLbl, textSpinner, "Detect & Redact Text"); }
});

// ── Render ────────────────────────────────────────────────────────────────
function render(data) {
    const rpt = data.report || {};
    const pii = rpt.pii_summary || {};
    const dets = rpt.detections || [];
    const by = pii.by_category || {};
    const total = pii.total_detected ?? dets.length;
    const conf = Math.round((pii.confidence_estimate || 0.9) * 100);

    resTitle.textContent = data.scan_only ? "Scan Complete (Not Redacted)" : "Redaction Complete";
    resMeta.textContent = `${(data.file_type || "").toUpperCase()} · ${total} entities detected · ${conf}% confidence`;

    resActions.innerHTML = "";
    if (data.redacted_file_b64 && !data.scan_only) {
        resActions.insertAdjacentHTML("beforeend", `<button class="btn-dl" onclick="b64dl()">Download File</button>`);
        window.__lastDownload = { b64: data.redacted_file_b64, name: "redacted_" + (data.filename || "output"), type: data.file_type };
    }
    resActions.insertAdjacentHTML("beforeend", `<button class="btn-rpt" onclick="rptDl()">JSON Report</button>`);
    window.__lastReport = data.report;

    statGrid.innerHTML = "";
    addStat(total, "Total PII");
    addStat(pii.regex_detections ?? "—", "Regex Hits");
    addStat(pii.nlp_detections ?? "—", "NLP Hits");
    addStat(`${conf}%`, "Confidence");

    lastRedacted = data.redacted_text || "";
    if (data.original_text != null) {
        renderDiff(data.original_text, lastRedacted || data.original_text, dets, "side");
        diffCard.classList.remove("hidden");
    } else {
        diffCard.classList.add("hidden");
    }

    tblBadge.textContent = dets.length;
    piiBody.innerHTML = "";
    dets.forEach((d, i) => {
        const isNlp = d.source === "nlp";
        const score = d.score ?? 1;
        piiBody.insertAdjacentHTML("beforeend", `
      <tr>
        <td style="color:var(--muted)">${i + 1}</td>
        <td><span class="tag ${isNlp ? "nlp" : ""}">${esc(d.entity_type)}</span></td>
        <td title="${esc(d.original_text)}">${esc(d.original_text || "—")}</td>
        <td><span class="src-${d.source || "regex"}">${d.source || "regex"}</span></td>
        <td><div class="score-wrap"><div class="score-bar"><div class="score-fill" style="width:${Math.round(score * 100)}%"></div></div><span class="score-pct">${Math.round(score * 100)}%</span></div></td>
      </tr>`);
    });

    bkBars.innerHTML = "";
    const maxC = Math.max(1, ...Object.values(by));
    if (Object.keys(by).length) {
        Object.entries(by).sort((a, b) => b[1] - a[1]).forEach(([k, c]) => {
            bkBars.insertAdjacentHTML("beforeend", `
        <div class="bk-row">
          <span class="bk-lbl">${esc(k)}</span>
          <div class="bk-track"><div class="bk-fill" style="width:${Math.round(c / maxC * 100)}%"></div></div>
          <span class="bk-count">${c}</span>
        </div>`);
        });
    } else {
        bkBars.innerHTML = `<p style="color:var(--muted);font-size:.8rem">No category data</p>`;
    }

    results.classList.remove("hidden");
    results.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

// ── Diff card ─────────────────────────────────────────────────────────────
window.showDiff = mode => {
    document.querySelectorAll(".dtab").forEach((t, i) => t.classList.toggle("active", ["side", "redacted", "original"][i] === mode));
    renderDiff(window.__origText || "", window.__redtText || "", window.__dets || [], mode);
};

function renderDiff(orig, redt, dets, mode) {
    window.__origText = orig; window.__redtText = redt; window.__dets = dets;
    const origHtml = highlightPII(orig, dets, "original");
    const redtHtml = highlightPII(redt, [], "redacted");
    if (mode === "side") {
        diffBody.className = "diff-body side";
        diffBody.innerHTML = `<div class="diff-pane"><div class="diff-lbl">Original</div><div class="diff-text">${origHtml}</div></div><div class="diff-pane"><div class="diff-lbl">Redacted</div><div class="diff-text">${redtHtml}</div></div>`;
    } else if (mode === "original") {
        diffBody.className = "diff-body";
        diffBody.innerHTML = `<div class="diff-pane"><div class="diff-lbl">Original</div><div class="diff-text">${origHtml}</div></div>`;
    } else {
        diffBody.className = "diff-body";
        diffBody.innerHTML = `<div class="diff-pane"><div class="diff-lbl">Redacted</div><div class="diff-text">${redtHtml}</div></div>`;
    }
}

function highlightPII(text, dets, mode) {
    if (!text) return "";
    if (mode === "redacted" || !dets.length) return esc(text);
    const sorted = [...dets].sort((a, b) => (a.start || 0) - (b.start || 0));
    let html = "", cursor = 0;
    for (const d of sorted) {
        const s = d.start ?? text.toLowerCase().indexOf((d.original_text || "").toLowerCase());
        const e = d.end ?? (s + (d.original_text || "").length);
        if (s < 0 || s < cursor) continue;
        html += esc(text.slice(cursor, s));
        html += `<span class="pii-span" title="${esc(d.entity_type)}">${esc(text.slice(s, e))}</span>`;
        cursor = e;
    }
    return html + esc(text.slice(cursor));
}

copyBtn.addEventListener("click", () => {
    if (!lastRedacted) return;
    navigator.clipboard.writeText(lastRedacted).then(() => {
        copyBtn.textContent = "Copied!"; copyBtn.classList.add("copied");
        setTimeout(() => { copyBtn.textContent = "Copy"; copyBtn.classList.remove("copied"); }, 2000);
    });
});

// ── Session history ───────────────────────────────────────────────────────
const HIST_KEY = "piiguard_history";

function addHistory(job) {
    let hist = getHistory();
    hist.unshift({ name: job.name, type: job.type, total: job.total, ts: Date.now() });
    hist = hist.slice(0, 5);
    localStorage.setItem(HIST_KEY, JSON.stringify(hist));
    renderHistory();
}

function getHistory() { try { return JSON.parse(localStorage.getItem(HIST_KEY) || "[]"); } catch { return []; } }

function renderHistory() {
    const hist = getHistory();
    if (!hist.length) { histList.innerHTML = `<p class="hist-empty">No jobs yet</p>`; return; }
    histList.innerHTML = hist.map(h => `
    <div class="hist-item">
      <div><div class="hist-name">${esc(h.name)}</div><div class="hist-info">${h.type.toUpperCase()} · ${h.total} entities · ${new Date(h.ts).toLocaleTimeString()}</div></div>
    </div>`).join("");
}
renderHistory();

// ── Helpers ───────────────────────────────────────────────────────────────
function addStat(val, lbl) {
    statGrid.insertAdjacentHTML("beforeend",
        `<div class="stat"><div class="stat-val">${esc(String(val))}</div><div class="stat-lbl">${lbl}</div></div>`);
}

function setLoad(on, labelEl, spinEl, offText) {
    if (activeMode === "file") redactBtn.disabled = on || !file;
    if (activeMode === "text") redactTextBtn.disabled = on;
    labelEl.textContent = on ? "Processing..." : (offText || labelEl.textContent);
    spinEl.classList.toggle("hidden", !on);
}

function showError(msg) { errorMsg.textContent = msg; errorBar.classList.remove("hidden"); }

window.b64dl = () => {
    const d = window.__lastDownload; if (!d) return;
    const mime = { csv: "text/csv", json: "application/json", txt: "text/plain", pdf: "application/pdf", png: "image/png", image: "image/png", jpg: "image/jpeg" }[d.type] || "application/octet-stream";
    dl(new Blob([Uint8Array.from(atob(d.b64), c => c.charCodeAt(0))], { type: mime }), d.name);
};
window.rptDl = () => { if (window.__lastReport) dl(new Blob([JSON.stringify(window.__lastReport, null, 2)], { type: "application/json" }), "pii_report.json"); };
function dl(blob, name) { const a = Object.assign(document.createElement("a"), { href: URL.createObjectURL(blob), download: name }); a.click(); URL.revokeObjectURL(a.href); }
