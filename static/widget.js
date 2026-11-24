(function () {
  if (window.__faqWebBotLoaded) return;
  window.__faqWebBotLoaded = true;

  var scriptEl = document.currentScript;
  var apiBase = (scriptEl && scriptEl.getAttribute("data-api")) || window.location.origin;
  var sessionId = "sess-" + Math.random().toString(36).slice(2, 10);

  var style = document.createElement("style");
  style.textContent =
    "#fwb-btn{position:fixed;right:20px;bottom:20px;z-index:9999;background:#111827;color:#fff;border:none;border-radius:999px;padding:12px 18px;font:600 14px system-ui,sans-serif;cursor:pointer;box-shadow:0 8px 24px rgba(0,0,0,.22)}" +
    "#fwb-box{position:fixed;right:20px;bottom:76px;z-index:9999;width:330px;max-width:calc(100vw - 32px);background:#fff;border:1px solid #e5e7eb;border-radius:14px;box-shadow:0 16px 40px rgba(0,0,0,.18);display:none;flex-direction:column;overflow:hidden;font:14px system-ui,sans-serif}" +
    "#fwb-head{background:#111827;color:#fff;padding:12px 14px;font-weight:600;display:flex;justify-content:space-between;align-items:center}" +
    "#fwb-log{height:240px;overflow-y:auto;padding:12px;display:flex;flex-direction:column;gap:8px;background:#f9fafb}" +
    ".fwb-m{padding:8px 11px;border-radius:10px;max-width:85%;line-height:1.35;white-space:pre-wrap}" +
    ".fwb-u{align-self:flex-end;background:#111827;color:#fff}" +
    ".fwb-b{align-self:flex-start;background:#fff;border:1px solid #e5e7eb;color:#111827}" +
    "#fwb-form{display:flex;border-top:1px solid #e5e7eb}" +
    "#fwb-in{flex:1;border:none;padding:10px 12px;outline:none;font:14px system-ui,sans-serif}" +
    "#fwb-send{border:none;background:#111827;color:#fff;padding:0 14px;cursor:pointer;font-weight:600}" +
    "#fwb-lead{display:none;padding:10px 12px;border-top:1px solid #e5e7eb;background:#fefce8;gap:6px;flex-direction:column}" +
    "#fwb-lead input{padding:7px 9px;border:1px solid #d1d5db;border-radius:6px;font:13px system-ui,sans-serif}" +
    "#fwb-lead button{background:#111827;color:#fff;border:none;border-radius:6px;padding:8px;cursor:pointer;font-weight:600}";
  document.head.appendChild(style);

  var btn = document.createElement("button");
  btn.id = "fwb-btn";
  btn.textContent = "💬 ¿Dudas? Pregúntanos";

  var box = document.createElement("div");
  box.id = "fwb-box";

  var head = document.createElement("div");
  head.id = "fwb-head";
  var title = document.createElement("span");
  title.textContent = "Asistente 24/7";
  var closeBtn = document.createElement("button");
  closeBtn.textContent = "✕";
  closeBtn.style.cssText = "background:none;border:none;color:#fff;cursor:pointer;font-size:15px";
  head.appendChild(title);
  head.appendChild(closeBtn);

  var log = document.createElement("div");
  log.id = "fwb-log";

  var leadBox = document.createElement("form");
  leadBox.id = "fwb-lead";
  var lName = document.createElement("input");
  lName.placeholder = "Tu nombre";
  lName.required = true;
  var lContact = document.createElement("input");
  lContact.placeholder = "WhatsApp o correo";
  lContact.required = true;
  var lBtn = document.createElement("button");
  lBtn.type = "submit";
  lBtn.textContent = "Enviar contacto";
  leadBox.appendChild(lName);
  leadBox.appendChild(lContact);
  leadBox.appendChild(lBtn);

  var form = document.createElement("form");
  form.id = "fwb-form";
  var input = document.createElement("input");
  input.id = "fwb-in";
  input.placeholder = "Escribe tu pregunta...";
  var send = document.createElement("button");
  send.id = "fwb-send";
  send.type = "submit";
  send.textContent = "Enviar";
  form.appendChild(input);
  form.appendChild(send);

  box.appendChild(head);
  box.appendChild(log);
  box.appendChild(leadBox);
  box.appendChild(form);
  document.body.appendChild(btn);
  document.body.appendChild(box);

  function addMsg(text, who) {
    var d = document.createElement("div");
    d.className = "fwb-m " + (who === "user" ? "fwb-u" : "fwb-b");
    d.textContent = text;
    log.appendChild(d);
    log.scrollTop = log.scrollHeight;
  }

  addMsg("¡Hola! Pregúntame por horarios, precios, entregas o medios de pago.", "bot");
  var lastQuestion = "";

  btn.onclick = function () {
    box.style.display = box.style.display === "flex" ? "none" : "flex";
  };
  closeBtn.onclick = function () {
    box.style.display = "none";
  };

  form.onsubmit = function (e) {
    e.preventDefault();
    var q = input.value.trim();
    if (!q) return;
    lastQuestion = q;
    addMsg(q, "user");
    input.value = "";
    var typing = document.createElement("div");
    typing.className = "fwb-m fwb-b";
    typing.textContent = "Escribiendo...";
    log.appendChild(typing);
    log.scrollTop = log.scrollHeight;
    fetch(apiBase.replace(/\/$/, "") + "/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, pregunta: q }),
    })
      .then(function (r) {
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.json();
      })
      .then(function (data) {
        if (typing.parentNode) typing.parentNode.removeChild(typing);
        addMsg(data.respuesta || "Sin respuesta.", "bot");
        if (data.sugerir_lead) leadBox.style.display = "flex";
      })
      .catch(function () {
        if (typing.parentNode) typing.parentNode.removeChild(typing);
        addMsg("No pude conectar con el servidor ahora.", "bot");
      });
  };

  leadBox.onsubmit = function (e) {
    e.preventDefault();
    fetch(apiBase.replace(/\/$/, "") + "/lead", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        nombre: lName.value.trim(),
        contacto: lContact.value.trim(),
        consulta: lastQuestion,
        origen: window.location.href,
      }),
    })
      .then(function (r) {
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.json();
      })
      .then(function () {
        leadBox.style.display = "none";
        lName.value = "";
        lContact.value = "";
        addMsg("✅ ¡Gracias! Guardamos tu contacto y te escribimos pronto.", "bot");
      })
      .catch(function () {
        addMsg("Error guardando tu contacto, intenta de nuevo.", "bot");
      });
  };
})();
