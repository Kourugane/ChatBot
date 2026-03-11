/**
 * chat.js — Lógica de frontend del Chatbot FAQ de Negocios (versión en español)
 *
 * Responsabilidades:
 *  - Enviar mensajes del usuario al endpoint Flask /chat
 *  - Renderizar burbujas de usuario y bot con marcas de tiempo
 *  - Mostrar indicador de escritura mientras espera la respuesta
 *  - Manejar clics en chips de sugerencia
 *  - Permitir envío con la tecla Enter
 */

"use strict";

/* ── Referencias al DOM ──────────────────────────────────────────── */
const chatWindow = document.getElementById("chatWindow");
const msgInput   = document.getElementById("msgInput");
const sendBtn    = document.getElementById("sendBtn");
const sugBar     = document.getElementById("suggestionBar");

/* ── Utilidades ──────────────────────────────────────────────────── */

/** Formatea una fecha como "HH:MM" */
function fmtTime(date) {
  return date.toLocaleTimeString("es-CO", { hour: "2-digit", minute: "2-digit" });
}

/** Desplaza la ventana de chat hasta el final */
function scrollToBottom() {
  chatWindow.scrollTo({ top: chatWindow.scrollHeight, behavior: "smooth" });
}

/** Escapa caracteres HTML especiales para evitar inyección de código */
function escHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/* ── Renderizado de burbujas ──────────────────────────────────────── */

/**
 * Agrega una burbuja de mensaje a la ventana de chat.
 * @param {string} text   - Contenido del mensaje
 * @param {string} role   - "user" | "bot"
 * @param {Date}  [time]  - Marca de tiempo (por defecto ahora)
 */
function appendMessage(text, role, time) {
  const ts   = time || new Date();
  const wrap = document.createElement("div");
  wrap.className = `message ${role === "user" ? "user-message" : "bot-message"}`;

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.innerHTML = escHtml(text).replace(/\n/g, "<br/>");

  const stamp = document.createElement("span");
  stamp.className = "msg-time";
  stamp.textContent = fmtTime(ts);

  wrap.appendChild(bubble);
  wrap.appendChild(stamp);
  chatWindow.appendChild(wrap);
  scrollToBottom();
  return wrap;
}

/** Muestra un indicador animado de "escribiendo..."; retorna el elemento para quitarlo después */
function showTyping() {
  const wrap = document.createElement("div");
  wrap.className = "message bot-message typing-bubble";
  wrap.innerHTML = `<div class="bubble"><div class="dots">
    <span></span><span></span><span></span>
  </div></div>`;
  chatWindow.appendChild(wrap);
  scrollToBottom();
  return wrap;
}

/* ── Lógica principal de envío ────────────────────────────────────── */

/** Desactiva o activa el campo de entrada y el botón durante una solicitud pendiente */
function setLoading(active) {
  sendBtn.disabled  = active;
  msgInput.disabled = active;
}

/**
 * Envía el mensaje del usuario a /chat y muestra la respuesta del bot.
 * @param {string} [override] - Texto opcional (desde chips de sugerencia)
 */
async function sendMessage(override) {
  const raw = (override || msgInput.value).trim();
  if (!raw) return;

  // Ocultar chips de sugerencia después de la primera interacción real
  if (sugBar) {
    sugBar.style.transition = "opacity .3s";
    sugBar.style.opacity = "0";
    setTimeout(() => { sugBar.style.display = "none"; }, 320);
  }

  msgInput.value = "";
  appendMessage(raw, "user");
  setLoading(true);

  const typingEl = showTyping();

  try {
    const res = await fetch("/chat", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ message: raw }),
    });

    if (!res.ok) throw new Error(`Error del servidor: ${res.status}`);

    const data = await res.json();
    typingEl.remove();

    const botText = data.response || "Lo siento, no pude procesar tu solicitud.";
    appendMessage(botText, "bot");

  } catch (err) {
    typingEl.remove();
    appendMessage(
      "⚠️ Error de conexión. Por favor verifica que el servidor esté en ejecución.",
      "bot"
    );
    console.error("[chat.js] Error de Fetch:", err);
  } finally {
    setLoading(false);
    msgInput.focus();
  }
}

/** Maneja clics en chips de sugerencia */
function sendSuggestion(btn) {
  sendMessage(btn.textContent.trim());
}

/* ── Listeners de eventos ─────────────────────────────────────────── */

// Enviar con Enter (no Shift+Enter)
msgInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

// Enfocar el campo de entrada al cargar la página
window.addEventListener("DOMContentLoaded", () => {
  msgInput.focus();
});
