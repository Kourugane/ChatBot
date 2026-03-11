"""
database.py — Operaciones SQLite para el Chatbot FAQ de Negocios
Gestiona creación de tablas, CRUD de base de conocimiento,
registro de conversaciones, analíticas y modo de entrenamiento.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "chatbot.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_base (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            question    TEXT    NOT NULL,
            answer      TEXT    NOT NULL,
            keywords    TEXT    NOT NULL,
            created_at  TEXT    DEFAULT (datetime('now', 'localtime')),
            updated_at  TEXT    DEFAULT (datetime('now', 'localtime'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_logs (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            message          TEXT    NOT NULL,
            response         TEXT    NOT NULL,
            similarity_score REAL    DEFAULT 0.0,
            matched_kb_id    INTEGER,
            session_id       TEXT    DEFAULT 'anon',
            timestamp        TEXT    DEFAULT (datetime('now', 'localtime'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS unanswered_questions (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            question  TEXT    NOT NULL,
            frequency INTEGER DEFAULT 1,
            timestamp TEXT    DEFAULT (datetime('now', 'localtime'))
        )
    """)

    conn.commit()

    if cursor.execute("SELECT COUNT(*) FROM knowledge_base").fetchone()[0] == 0:
        _seed_spanish_data(cursor)
        conn.commit()
        print("[BD] Entradas en espanol insertadas.")

    conn.close()
    print("[BD] Base de datos inicializada correctamente.")


def _seed_spanish_data(cursor):
    entradas = [
        ("cuál es el horario de atención",
         "Estamos abiertos de lunes a viernes de 8:00 AM a 10:00 PM, y fines de semana de 9:00 AM a 11:00 PM. Los festivos abrimos de 10:00 AM a 8:00 PM.",
         "horario, horas, abierto, cerrado, atención, apertura, cierre, cuándo, hora, abre, cierra, funciona"),
        ("dónde están ubicados",
         "Nos encontramos en la Calle 45 #12-30, Chapinero, Bogotá. A media cuadra del Parque de la 45. Contamos con parqueadero propio.",
         "ubicación, dirección, dónde, cómo llegar, lugar, sitio, localización, encontrar, mapa, donde"),
        ("hacen domicilios",
         "¡Sí! Realizamos domicilios dentro de un radio de 10 km. El tiempo estimado es de 30 a 45 minutos. Pedido mínimo $15.000. Puedes pedir por WhatsApp o llamándonos.",
         "domicilio, entrega, delivery, envío, llevar, despacho, reparto, a casa, pedir, pedido, servicio entrega"),
        ("aceptan reservas",
         "Sí, aceptamos reservas para grupos desde 2 personas. Puedes reservar por teléfono, WhatsApp o nuestra página web. Para grupos grandes (+10 personas) recomendamos reservar con 48 horas de anticipación.",
         "reserva, reservar, mesa, cita, apartar, booking, agendar, grupo, reservación"),
        ("qué formas de pago aceptan",
         "Aceptamos efectivo, tarjetas de crédito y débito (Visa, Mastercard, Amex), transferencia bancaria, Nequi y Daviplata. No aceptamos cheques.",
         "pago, pagar, tarjeta, efectivo, crédito, débito, visa, mastercard, nequi, daviplata, transferencia, forma de pago"),
        ("tienen opciones vegetarianas o veganas",
         "¡Claro que sí! Contamos con sección vegetariana y vegana en nuestro menú, claramente identificada. Si tienes alguna restricción alimentaria, infórmale a nuestro personal.",
         "vegetariano, vegano, sin carne, dieta, alérgeno, gluten, restricción, alimentación, saludable"),
        ("qué tiene el menú",
         "Nuestro menú incluye desayunos, almuerzos ejecutivos ($12.000–$18.000), cenas, bebidas calientes y frías, y postres artesanales. Visita nuestra web o pídenos la carta por WhatsApp.",
         "menú, carta, platos, comida, alimentos, qué sirven, qué tienen, opciones, plato del día, almuerzo, desayuno, cena, precio"),
        ("tienen promociones o descuentos",
         "¡Sí! Ofrecemos: 10% de descuento los martes, combo ejecutivo de L–V de 12PM a 3PM, 15% de descuento para estudiantes con carnet, y 2x1 en bebidas los jueves. Síguenos en redes para más promos.",
         "promoción, descuento, oferta, promo, combo, especial, precio, rebaja, estudiante, beneficio, cupón"),
        ("cómo puedo contactarlos",
         "Puedes contactarnos por: Teléfono: +57 (1) 234-5678 | WhatsApp: +57 300 123 4567 | Email: hola@restaurante.com | O por nuestra página web. Atendemos de L–S de 8AM a 9PM.",
         "contacto, teléfono, llamar, whatsapp, correo, email, comunicar, hablar, número, mensaje, contactar"),
        ("hay parqueadero",
         "Sí, contamos con parqueadero propio con capacidad para 20 vehículos. Las primeras 2 horas son gratis para clientes. Después $2.000 por hora. También hay parqueadero público a media cuadra.",
         "parqueadero, parking, estacionamiento, carro, vehículo, aparcar, parquear, moto, bicicleta, espacio"),
        ("hacen eventos y celebraciones",
         "¡Sí! Ofrecemos servicio de catering y espacios para eventos corporativos, cumpleaños y matrimonios. Tenemos salón privado para 50 personas. Contáctanos con mínimo una semana de anticipación.",
         "evento, celebración, fiesta, cumpleaños, matrimonio, corporativo, catering, grupo, salón, reunión"),
        ("tienen wifi",
         "Sí, ofrecemos Wi-Fi gratuito para todos nuestros clientes. La clave está en cada mesa o pídela al personal. Red: Restaurante_WiFi | Clave: bienvenido2024.",
         "wifi, internet, red, contraseña, clave, conectar, conexión, señal"),
        ("cuánto tiempo demora el pedido",
         "En el local, los platos se sirven en 15 a 25 minutos. Para domicilios, el tiempo estimado es 30 a 45 minutos según la distancia. En horas pico puede haber una pequeña espera adicional.",
         "tiempo, demora, espera, cuánto tarda, minutos, rapidez, pedido, entrega, servicio"),
        ("tienen menú infantil",
         "Sí, contamos con menú especial para niños con porciones más pequeñas, opciones nutritivas y precios especiales desde $8.000. También tenemos sillas para bebés. ¡Los niños son bienvenidos!",
         "niños, infantil, menú infantil, kids, pequeños, bebés, silla, niño, hijo, familia"),
        ("cómo hago un pedido en línea",
         "Puedes hacer tu pedido en línea por: nuestra web (restaurante.com), WhatsApp al +57 300 123 4567, o por teléfono al +57 (1) 234-5678. Aceptamos pedidos anticipados con hasta 24 horas de anticipación.",
         "pedido online, pedir en línea, ordenar, web, internet, página web, en línea, online, aplicación"),
        ("tienen productos para llevar",
         "Sí, todos nuestros platos están disponibles para llevar (to-go). Solo dinos cuándo pasarás a recoger y tendremos tu pedido listo. Puedes ordenar con anticipación por WhatsApp.",
         "llevar, para llevar, take away, to go, recoger, empacar, domicilio"),
        ("tienen opciones sin gluten",
         "Sí, contamos con opciones sin gluten en nuestro menú. Por favor infórmale a tu mesero sobre cualquier alergia antes de ordenar. Tomamos precauciones especiales para evitar contaminación cruzada.",
         "gluten, celiaco, intolerancia, alergia, sin gluten, gluten-free, trigo, restricción"),
        ("cuál es la política de devoluciones",
         "Si tu pedido no cumple tus expectativas o hay un error, contáctanos dentro de las 24 horas. Ofrecemos reposición o reembolso completo. Para domicilios, puede solicitarse evidencia fotográfica.",
         "devolución, reembolso, política, queja, error, cambio, reclamación, retorno, dinero"),
    ]

    cursor.executemany(
        "INSERT INTO knowledge_base (question, answer, keywords) VALUES (?, ?, ?)",
        entradas
    )


# ── Knowledge Base CRUD ────────────────────────────────────────────────────────

def get_all_kb_entries():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM knowledge_base ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_kb_entry_by_id(entry_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM knowledge_base WHERE id = ?", (entry_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def add_kb_entry(question, answer, keywords):
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO knowledge_base (question, answer, keywords) VALUES (?, ?, ?)",
        (question.strip(), answer.strip(), keywords.strip())
    )
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id


def update_kb_entry(entry_id, question, answer, keywords):
    conn = get_connection()
    conn.execute(
        """UPDATE knowledge_base
           SET question=?, answer=?, keywords=?, updated_at=datetime('now','localtime')
           WHERE id=?""",
        (question.strip(), answer.strip(), keywords.strip(), entry_id)
    )
    conn.commit()
    conn.close()


def delete_kb_entry(entry_id):
    conn = get_connection()
    conn.execute("DELETE FROM knowledge_base WHERE id = ?", (entry_id,))
    conn.commit()
    conn.close()


# ── Chat Logs ─────────────────────────────────────────────────────────────────

def log_chat(session_id, user_message, bot_response,
             similarity_score=0.0, matched_kb_id=None):
    conn = get_connection()
    conn.execute(
        """INSERT INTO chat_logs (session_id, message, response, similarity_score, matched_kb_id)
           VALUES (?, ?, ?, ?, ?)""",
        (session_id, user_message, bot_response, round(similarity_score, 4), matched_kb_id)
    )
    conn.commit()
    conn.close()


def get_chat_log(limit=100):
    conn = get_connection()
    rows = conn.execute("SELECT * FROM chat_logs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Analíticas ─────────────────────────────────────────────────────────────────

def get_analytics():
    conn = get_connection()
    total    = conn.execute("SELECT COUNT(*) FROM chat_logs").fetchone()[0]
    answered = conn.execute("SELECT COUNT(*) FROM chat_logs WHERE matched_kb_id IS NOT NULL").fetchone()[0]
    unanswered_q = conn.execute("SELECT COUNT(*) FROM unanswered_questions").fetchone()[0]

    top_rows = conn.execute("""
        SELECT message, COUNT(*) as freq
        FROM chat_logs
        GROUP BY lower(trim(message))
        ORDER BY freq DESC
        LIMIT 10
    """).fetchall()

    recent_rows = conn.execute("""
        SELECT message, response, timestamp, similarity_score
        FROM chat_logs ORDER BY id DESC LIMIT 10
    """).fetchall()

    conn.close()
    return {
        "total":         total,
        "answered":      answered,
        "unanswered":    total - answered,
        "unanswered_q":  unanswered_q,
        "top_questions": [dict(r) for r in top_rows],
        "recent":        [dict(r) for r in recent_rows],
    }


# ── Preguntas sin respuesta ────────────────────────────────────────────────────

def add_unanswered(question):
    conn = get_connection()
    existing = conn.execute(
        "SELECT id FROM unanswered_questions WHERE lower(trim(question))=lower(trim(?))",
        (question,)
    ).fetchone()
    if existing:
        conn.execute("UPDATE unanswered_questions SET frequency=frequency+1 WHERE id=?", (existing["id"],))
    else:
        conn.execute("INSERT INTO unanswered_questions (question) VALUES (?)", (question.strip(),))
    conn.commit()
    conn.close()


def get_unanswered_questions():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM unanswered_questions ORDER BY frequency DESC, id DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_unanswered(uq_id):
    conn = get_connection()
    conn.execute("DELETE FROM unanswered_questions WHERE id = ?", (uq_id,))
    conn.commit()
    conn.close()
