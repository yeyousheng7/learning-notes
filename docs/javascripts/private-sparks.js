/* Decrypt locally; only a derived key is kept for this tab's session. */
(() => {
  "use strict";
  const section = document.querySelector(".sparks-private");
  if (!section) return;
  const payload = JSON.parse(section.querySelector(".sparks-payload").textContent);
  const form = section.querySelector("form");
  const input = form.querySelector("input");
  const submit = form.querySelector("button");
  const status = form.querySelector('[role="status"]');
  const unlocked = section.querySelector(".sparks-unlocked");
  const content = section.querySelector(".sparks-private__body");
  const relock = section.querySelector(".sparks-relock");
  const encoder = new TextEncoder();
  const storageKey = "private-sparks:" + new URL("../", document.currentScript.src).href;
  let generation = 0;

  const fromBase64 = value => Uint8Array.from(atob(value), char => char.charCodeAt(0));
  const toBase64 = value => btoa(String.fromCharCode(...new Uint8Array(value)));
  const clearSession = () => {
    try { sessionStorage.removeItem(storageKey); } catch (_) { /* Storage can be disabled. */ }
  };
  const importKey = raw => crypto.subtle.importKey("raw", raw, "AES-GCM", false, ["decrypt"]);

  async function decrypt(key) {
    const plain = await crypto.subtle.decrypt({
      name: "AES-GCM", iv: fromBase64(payload.nonce),
      additionalData: encoder.encode("private-spark:v1:" + payload.id), tagLength: 128
    }, key, fromBase64(payload.ciphertext));
    return new TextDecoder("utf-8", { fatal: true }).decode(plain);
  }

  function show(html, focus) {
    content.innerHTML = html;
    input.value = "";
    input.removeAttribute("aria-invalid");
    form.hidden = true;
    unlocked.hidden = false;
    if (focus) content.focus();
    if (window.MathJax?.typesetPromise) window.MathJax.typesetPromise([content]).catch(() => {});
  }

  function lock(focus = false) {
    generation += 1;
    clearSession();
    if (window.MathJax?.typesetClear) window.MathJax.typesetClear([content]);
    content.replaceChildren();
    unlocked.hidden = true;
    form.hidden = false;
    status.textContent = "解锁后，本标签页内的其他加密文章也会自动解锁。";
    if (focus) input.focus();
  }

  if (!window.isSecureContext || !window.crypto?.subtle) {
    status.textContent = "请通过 HTTPS 或本机预览地址打开此页面后解锁。";
    submit.disabled = true;
    return;
  }

  form.addEventListener("submit", async event => {
    event.preventDefault();
    const current = ++generation;
    submit.disabled = true;
    submit.textContent = "解锁中…";
    status.textContent = "正在解锁…";
    input.removeAttribute("aria-invalid");
    try {
      const password = await crypto.subtle.importKey("raw", encoder.encode(input.value), "PBKDF2", false, ["deriveBits"]);
      input.value = "";
      const raw = await crypto.subtle.deriveBits({
        name: "PBKDF2", hash: "SHA-256", salt: fromBase64(payload.salt), iterations: payload.iterations
      }, password, 256);
      const html = await decrypt(await importKey(raw));
      if (generation !== current) return;
      try {
        sessionStorage.setItem(storageKey, JSON.stringify({ salt: payload.salt, key: toBase64(raw) }));
      } catch (_) { /* Reading still works if session storage is unavailable. */ }
      show(html, true);
    } catch (_) {
      if (generation !== current) return;
      input.setAttribute("aria-invalid", "true");
      status.textContent = "密码不正确，或文章数据已损坏，请重试。";
      input.focus();
    } finally {
      submit.disabled = false;
      submit.textContent = "解锁";
    }
  });

  relock.addEventListener("click", () => lock(true));

  async function restore() {
    const current = generation;
    try {
      const cached = JSON.parse(sessionStorage.getItem(storageKey) || "null");
      if (!cached || cached.salt !== payload.salt) return;
      const html = await decrypt(await importKey(fromBase64(cached.key)));
      if (generation === current) show(html, false);
    } catch (_) { clearSession(); }
  }

  // Do not leave plaintext in a page restored from the back/forward cache.
  window.addEventListener("pagehide", () => {
    generation += 1;
    content.replaceChildren();
    unlocked.hidden = true;
    form.hidden = false;
    input.value = "";
  });
  window.addEventListener("pageshow", event => { if (event.persisted) restore(); });
  restore();
})();
