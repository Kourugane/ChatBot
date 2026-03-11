"""
app.py — Aplicación Flask principal del Chatbot FAQ de Negocios (versión mejorada)

Rutas:
  GET  /                        → Interfaz de chat al cliente
  POST /chat                    → API JSON: recibe mensaje, devuelve respuesta
  GET  /admin                   → Panel admin: gestión de base de conocimiento
  POST /admin/add               → Agregar nueva entrada
  POST /admin/edit/<id>         → Editar entrada existente
  POST /admin/delete/<id>       → Eliminar entrada
  GET  /admin/analytics         → Página de analíticas
  GET  /admin/training          → Modo entrenamiento: preguntas sin respuesta
  POST /admin/training/convert  → Convertir pregunta sin respuesta a entrada KB
  POST /admin/training/delete   → Eliminar pregunta sin respuesta
"""

import uuid
import logging
from flask import (
    Flask, render_template, request,
    jsonify, redirect, url_for, session, flash
)

from database import (
    init_db,
    get_all_kb_entries, get_kb_entry_by_id,
    add_kb_entry, update_kb_entry, delete_kb_entry,
    log_chat, get_chat_log,
    get_analytics,
    get_unanswered_questions, delete_unanswered,
)
from chatbot_engine import get_response

# ── Configuración de la app ────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = "cambia-esto-en-produccion"

logging.basicConfig(
    format="%(asctime)s  \033[36m%(levelname)-8s\033[0m  %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO,
)
log = logging.getLogger("app")

with app.app_context():
    init_db()


# ── Rutas del chat ─────────────────────────────────────────────────────────────

@app.route("/")
def index():
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True)
    if not data or not data.get("message", "").strip():
        return jsonify({"error": "Mensaje vacío"}), 400

    user_msg   = data["message"].strip()
    session_id = session.get("session_id", "anon")

    result = get_response(user_msg)

    try:
        log_chat(
            session_id       = session_id,
            user_message     = user_msg,
            bot_response     = result["answer"],
            similarity_score = result["score"],
            matched_kb_id    = result["matched_id"],
        )
    except Exception as exc:
        log.warning("No se pudo escribir en chat_logs: %s", exc)

    return jsonify({
        "response": result["answer"],
        "score":    result["score"],
        "matched":  result["matched_question"],
        "answered": result.get("answered", False),
    })


# ── Panel de administración — Base de conocimiento ────────────────────────────

@app.route("/admin")
def admin():
    entries = get_all_kb_entries()
    return render_template("admin.html", entries=entries)


@app.route("/admin/add", methods=["POST"])
def admin_add():
    question = request.form.get("question", "").strip()
    answer   = request.form.get("answer",   "").strip()
    keywords = request.form.get("keywords", "").strip()

    if not all([question, answer, keywords]):
        flash("Todos los campos son obligatorios.", "error")
        return redirect(url_for("admin"))

    new_id = add_kb_entry(question, answer, keywords)
    log.info("\033[32m[ADMIN]\033[0m Entrada agregada id=%d: %r", new_id, question)
    flash(f'Entrada "{question[:60]}" agregada correctamente.', "success")
    return redirect(url_for("admin"))


@app.route("/admin/edit/<int:entry_id>", methods=["POST"])
def admin_edit(entry_id):
    question = request.form.get("question", "").strip()
    answer   = request.form.get("answer",   "").strip()
    keywords = request.form.get("keywords", "").strip()

    if not all([question, answer, keywords]):
        flash("Todos los campos son obligatorios.", "error")
        return redirect(url_for("admin"))

    if not get_kb_entry_by_id(entry_id):
        flash("Entrada no encontrada.", "error")
        return redirect(url_for("admin"))

    update_kb_entry(entry_id, question, answer, keywords)
    log.info("\033[33m[ADMIN]\033[0m Entrada actualizada id=%d", entry_id)
    flash("Entrada actualizada correctamente.", "success")
    return redirect(url_for("admin"))


@app.route("/admin/delete/<int:entry_id>", methods=["POST"])
def admin_delete(entry_id):
    entry = get_kb_entry_by_id(entry_id)
    if not entry:
        flash("Entrada no encontrada.", "error")
        return redirect(url_for("admin"))

    delete_kb_entry(entry_id)
    log.info("\033[31m[ADMIN]\033[0m Entrada eliminada id=%d", entry_id)
    flash("Entrada eliminada.", "success")
    return redirect(url_for("admin"))


# ── Analíticas ─────────────────────────────────────────────────────────────────

@app.route("/admin/analytics")
def admin_analytics():
    stats = get_analytics()
    return render_template("analytics.html", stats=stats)


# ── Modo Entrenamiento ─────────────────────────────────────────────────────────

@app.route("/admin/training")
def admin_training():
    questions = get_unanswered_questions()
    return render_template("training.html", questions=questions)


@app.route("/admin/training/convert", methods=["POST"])
def training_convert():
    uq_id    = request.form.get("uq_id", "").strip()
    question = request.form.get("question", "").strip()
    answer   = request.form.get("answer",   "").strip()
    keywords = request.form.get("keywords", "").strip()

    if not all([uq_id, question, answer, keywords]):
        flash("Todos los campos son obligatorios para convertir la pregunta.", "error")
        return redirect(url_for("admin_training"))

    new_id = add_kb_entry(question, answer, keywords)
    delete_unanswered(int(uq_id))
    log.info("\033[32m[ENTRENAMIENTO]\033[0m Convertida a KB id=%d: %r", new_id, question)
    flash(f'Pregunta convertida y agregada a la base de conocimiento (id={new_id}).', "success")
    return redirect(url_for("admin_training"))


@app.route("/admin/training/delete", methods=["POST"])
def training_delete():
    uq_id = request.form.get("uq_id", "").strip()
    if uq_id:
        delete_unanswered(int(uq_id))
        flash("Pregunta eliminada del listado.", "success")
    return redirect(url_for("admin_training"))


@app.route("/admin/logs")
def admin_logs():
    return jsonify(get_chat_log(limit=100))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
