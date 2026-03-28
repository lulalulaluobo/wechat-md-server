(function () {
  /* ── HTML Escape ── */
  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function prettyJson(value) {
    return JSON.stringify(value ?? {}, null, 2);
  }

  /* ── Toast System ── */
  let toastContainer = null;
  function ensureToastContainer() {
    if (!toastContainer) {
      toastContainer = document.createElement("div");
      toastContainer.className = "toast-container";
      document.body.appendChild(toastContainer);
    }
    return toastContainer;
  }

  function toast(message, tone, duration) {
    const container = ensureToastContainer();
    const el = document.createElement("div");
    el.className = `toast ${tone || "info"}`;
    el.textContent = message;
    container.appendChild(el);
    setTimeout(() => {
      el.classList.add("fade-out");
      setTimeout(() => el.remove(), 180);
    }, duration || 3500);
  }

  /* ── Result Panel Builder ── */
  function resultHtml(options) {
    const tone = options.tone || "info";
    const title = escapeHtml(options.title || "");
    const desc = options.description ? `<p class="result-desc">${escapeHtml(options.description)}</p>` : "";
    const items = (options.items || [])
      .map(
        (item) =>
          `<div class="result-item"><span class="label">${escapeHtml(item.label)}</span><span class="value">${escapeHtml(item.value ?? "-")}</span></div>`
      )
      .join("");
    const json = options.json
      ? `<details class="json-viewer"><summary>原始 JSON</summary><pre>${escapeHtml(typeof options.json === "string" ? options.json : prettyJson(options.json))}</pre></details>`
      : "";
    return `<div class="result-block ${tone}"><p class="result-title">${title}</p>${desc}<div class="result-items">${items}</div>${json}</div>`;
  }

  /* ── DOM Helpers ── */
  function setHtml(id, html) {
    const el = document.getElementById(id);
    if (el) el.innerHTML = html;
  }

  function setText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
  }

  /* ── Advanced Toggle ── */
  function initAdvancedToggles() {
    document.querySelectorAll("[data-toggle-advanced]").forEach((btn) => {
      const targetId = btn.getAttribute("data-toggle-advanced");
      const panel = document.getElementById(targetId);
      if (!panel) return;
      btn.addEventListener("click", () => {
        const expanded = btn.getAttribute("aria-expanded") === "true";
        btn.setAttribute("aria-expanded", String(!expanded));
        panel.classList.toggle("open", !expanded);
      });
    });
  }

  /* ── Tab System ── */
  function initTabs() {
    document.querySelectorAll("[data-tab-group]").forEach((nav) => {
      const group = nav.getAttribute("data-tab-group");
      const buttons = nav.querySelectorAll(".tab-btn");
      buttons.forEach((btn) => {
        btn.addEventListener("click", () => {
          buttons.forEach((b) => b.classList.remove("active"));
          btn.classList.add("active");
          const target = btn.getAttribute("data-tab");
          document.querySelectorAll(`[data-tab-panel="${group}"]`).forEach((panel) => {
            panel.classList.toggle("active", panel.getAttribute("data-tab-id") === target);
          });
        });
      });
    });
  }

  /* ── Export ── */
  window.AdminUI = {
    escapeHtml,
    prettyJson,
    toast,
    resultHtml,
    setHtml,
    setText,
    initAdvancedToggles,
    initTabs,
  };
})();
