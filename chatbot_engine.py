"""
chatbot_engine.py — Motor de coincidencia inteligente (versión mejorada)

Estrategia de coincidencia (en capas, de más rápida a más lenta):
  1. Coincidencia exacta de pregunta (sin distinción de mayúsculas)
  2. Similitud de texto completo con difflib (umbral: 0.5 — Tarea 6)
  3. Solapamiento de palabras clave con extensión de prefijo-raíz
  4. Similitud difflib sobre texto de pregunta
  5. Similitud difflib sobre cadena de palabras clave

Todas las capas contribuyen a una puntuación combinada [0.0–1.0].
Umbral mínimo para responder: 0.28
"""

import re
import difflib
import logging
from database import get_all_kb_entries, add_unanswered

# ── Logging con colores ────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s  \033[36m%(levelname)-8s\033[0m  %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO,
)
log = logging.getLogger("chatbot_engine")

# ── Constantes ─────────────────────────────────────────────────────────────────
MATCH_THRESHOLD    = 0.28   # puntuación mínima para devolver una respuesta
DIFFLIB_THRESHOLD  = 0.50   # umbral de similitud directa (Tarea 6)
KEYWORD_WEIGHT     = 0.45
QUESTION_WEIGHT    = 0.30
KW_STR_WEIGHT      = 0.15
DIFFLIB_FULL_WEIGHT= 0.10

FALLBACK = (
    "Lo siento, no tengo información sobre eso todavía. "
    "Por favor contacta a nuestro personal directamente y con gusto te ayudarán. 😊"
)

# Palabras vacías en español para eliminar antes de comparar
STOP_WORDS = {
    "el", "la", "los", "las", "un", "una", "unos", "unas",
    "de", "del", "al", "en", "y", "o", "a", "que", "qué",
    "es", "son", "se", "su", "sus", "me", "te", "nos",
    "por", "para", "con", "sin", "como", "más", "si",
    "hay", "tienen", "tiene", "hacen", "hace", "puedo",
    "pueden", "quiero", "quisiera", "cuál", "cuáles",
    "cómo", "dónde", "cuándo", "cuánto", "cuántos",
    "mi", "mis", "tu", "tus", "le", "les", "lo", "este",
    "esta", "esto", "eso", "ese", "esa", "aquí", "allá",
    "hola", "buenos", "días", "tardes", "noches", "gracias",
    "por favor", "favor", "saben", "sabe", "quieren",
    "the", "a", "an", "is", "in", "on", "at", "to", "for",
    "of", "and", "or", "do", "you", "we", "are", "has",
}


# ── Utilidades de texto ────────────────────────────────────────────────────────

def _clean(text: str) -> str:
    """Minúsculas, eliminar puntuación, colapsar espacios."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _tokenise(text: str) -> set:
    """Tokens significativos tras eliminar palabras vacías."""
    return {w for w in _clean(text).split() if w not in STOP_WORDS and len(w) > 1}


def _seq_sim(a: str, b: str) -> float:
    """Ratio de SequenceMatcher de difflib entre dos cadenas."""
    return difflib.SequenceMatcher(None, a, b).ratio()


# ── Lógica de puntuación ───────────────────────────────────────────────────────

def _score_entry(user_tokens: set, user_clean: str, entry: dict) -> float:
    """Calcula una puntuación combinada [0.0–1.0] para una entrada de la BD."""
    q_clean   = _clean(entry["question"])
    kw_tokens = _tokenise(entry["keywords"])
    kw_string = _clean(entry["keywords"])

    # Capa 1 — Coincidencia exacta
    if user_clean == q_clean:
        return 1.0

    # Capa 2 — Similitud de texto completo con difflib (Tarea 6)
    # Si la pregunta del usuario es muy similar a la pregunta almacenada,
    # devolvemos directamente aunque los tokens no coincidan exactamente.
    full_sim = _seq_sim(user_clean, q_clean)
    if full_sim >= DIFFLIB_THRESHOLD:
        # Puntuación alta garantizada, ponderada levemente por keywords
        kw_bonus = len(user_tokens & kw_tokens) / max(len(user_tokens | kw_tokens), 1)
        return min(1.0, full_sim * 0.85 + kw_bonus * 0.15)

    # Capa 3 — Solapamiento de palabras clave con extensión de prefijo-raíz
    extended_kw = set(kw_tokens)
    for ut in user_tokens:
        for kt in kw_tokens:
            if len(ut) > 3 and len(kt) > 3:
                if ut.startswith(kt[:4]) or kt.startswith(ut[:4]):
                    extended_kw.add(ut)

    if extended_kw:
        overlap = len(user_tokens & extended_kw) / len(user_tokens | extended_kw)
    else:
        overlap = 0.0

    # Capa 4 — Similitud difflib sobre texto de pregunta
    q_sim  = _seq_sim(user_clean, q_clean)

    # Capa 5 — Similitud difflib sobre cadena de palabras clave
    kw_sim = _seq_sim(user_clean, kw_string)

    blended = (
        KEYWORD_WEIGHT      * overlap  +
        QUESTION_WEIGHT     * q_sim    +
        KW_STR_WEIGHT       * kw_sim   +
        DIFFLIB_FULL_WEIGHT * full_sim
    )
    return blended


# ── Punto de entrada principal ─────────────────────────────────────────────────

def get_response(user_message: str) -> dict:
    """
    Procesa un mensaje y devuelve la mejor respuesta disponible.

    Devuelve:
        {
            "answer":           str,
            "score":            float,
            "matched_id":       int | None,
            "matched_question": str | None,
            "answered":         bool
        }
    """
    user_clean  = _clean(user_message)
    user_tokens = _tokenise(user_message)

    if not user_clean:
        return {
            "answer": "Por favor escribe tu pregunta y haré lo posible por ayudarte. 😊",
            "score": 0.0, "matched_id": None,
            "matched_question": None, "answered": False,
        }

    entries = get_all_kb_entries()

    if not entries:
        log.warning("La base de conocimiento está vacía.")
        return {
            "answer": FALLBACK, "score": 0.0,
            "matched_id": None, "matched_question": None, "answered": False,
        }

    scored = [
        (entry, _score_entry(user_tokens, user_clean, entry))
        for entry in entries
    ]
    scored.sort(key=lambda x: x[1], reverse=True)
    best_entry, best_score = scored[0]

    log.info(
        "\033[33mUsuario:\033[0m %s  →  \033[32mpuntuación=%.3f\033[0m  coincidencia=%r",
        user_message, best_score,
        best_entry["question"] if best_score >= MATCH_THRESHOLD else "SIN COINCIDENCIA"
    )

    if best_score >= MATCH_THRESHOLD:
        return {
            "answer":           best_entry["answer"],
            "score":            round(best_score, 4),
            "matched_id":       best_entry["id"],
            "matched_question": best_entry["question"],
            "answered":         True,
        }

    # Sin coincidencia — guardar para entrenamiento
    try:
        add_unanswered(user_message)
        log.info("\033[31m[ENTRENAMIENTO]\033[0m Pregunta sin respuesta guardada: %r", user_message)
    except Exception as exc:
        log.warning("No se pudo guardar pregunta sin respuesta: %s", exc)

    return {
        "answer":           FALLBACK,
        "score":            round(best_score, 4),
        "matched_id":       None,
        "matched_question": None,
        "answered":         False,
    }
