# 🍽️ Chatbot FAQ de Negocios — Asistente Virtual Inteligente

Sistema de chatbot de atención al cliente completamente local, construido con **Python (Flask)**, **SQLite** y **HTML/CSS/JS**. Diseñado para pequeños negocios —restaurantes, tiendas, servicios de reparación— que desean automatizar sus preguntas frecuentes en español.

---

## ¿Qué hace este proyecto?

El sistema permite a un negocio crear y gestionar una **base de conocimiento** de preguntas y respuestas frecuentes. Cuando un cliente escribe una pregunta, el chatbot:

1. Limpia y procesa el texto
2. Busca la respuesta más similar usando múltiples capas de análisis
3. Devuelve la respuesta correcta o indica que contacte al personal
4. Registra la conversación para analíticas y mejora continua

---

## Estructura del proyecto

```
business_chatbot/
├── app.py                # Rutas Flask y lógica de servidor
├── chatbot_engine.py     # Motor de coincidencia inteligente
├── database.py           # Operaciones SQLite (CRUD completo)
├── chatbot.db            # Base de datos (se crea automáticamente)
├── templates/
│   ├── index.html        # Interfaz de chat para clientes
│   ├── admin.html        # Panel de administración — Base de conocimiento
│   ├── analytics.html    # Panel de analíticas
│   └── training.html     # Modo de entrenamiento
├── static/
│   ├── style.css         # Estilos (tema oscuro cálido)
│   └── chat.js           # Lógica del chat en el navegador
└── README.md
```

---

## Cómo ejecutar el sistema localmente

### 1. Requisitos previos

- Python 3.8 o superior
- `pip` (gestor de paquetes de Python)

### 2. Instalar dependencias

```bash
pip install flask
```

> Flask es la **única** dependencia externa. Todo lo demás (`sqlite3`, `difflib`, `re`, `logging`, `uuid`) forma parte de la biblioteca estándar de Python.

### 3. Iniciar el servidor

```bash
cd business_chatbot
python app.py
```

Verás algo así en la terminal:

```
[BD] Entradas en español insertadas.
[BD] Base de datos inicializada correctamente.
 * Running on http://127.0.0.1:5000
```

### 4. Abrir la aplicación

| Página                    | URL                                |
|---------------------------|------------------------------------|
| Chat para clientes        | http://127.0.0.1:5000/             |
| Base de conocimiento      | http://127.0.0.1:5000/admin        |
| Analíticas                | http://127.0.0.1:5000/admin/analytics |
| Modo entrenamiento        | http://127.0.0.1:5000/admin/training  |

---

## Cómo funciona el chatbot

### Motor de coincidencia (5 capas)

El motor analiza cada pregunta del usuario contra todas las entradas de la base de conocimiento usando un sistema de puntuación en capas:

| Capa | Descripción | Peso |
|------|-------------|------|
| 1 — Coincidencia exacta | Si el texto limpio coincide perfectamente | 100% inmediato |
| 2 — Similitud difflib completa | `SequenceMatcher` entre la pregunta del usuario y la almacenada (Tarea 6) | Umbral 0.50 |
| 3 — Solapamiento de palabras clave | Índice de Jaccard con extensión de prefijo-raíz | 45% |
| 4 — Similitud sobre texto de pregunta | `difflib` sobre texto limpio | 30% |
| 5 — Similitud sobre cadena de keywords | `difflib` sobre palabras clave | 25% |

**Umbral mínimo:** Si la puntuación combinada es ≥ 0.28, se devuelve la mejor respuesta. Si no, se guarda la pregunta para entrenamiento.

### Palabras vacías en español

El motor elimina palabras comunes del español ("el", "la", "de", "qué", "cómo", etc.) antes de comparar, para que "¿Cuál es el horario?" y "horario" generen tokens similares.

### Extensión de prefijo-raíz

Si el usuario escribe "domicilios" y la palabra clave almacenada es "domicilio", el motor los reconoce como equivalentes mediante comparación de los primeros 4 caracteres del token.

---

## Cómo usar el Panel de Administración

### Base de conocimiento (`/admin`)

1. **Agregar entrada:** Clic en `+ Agregar Entrada`, completa pregunta, respuesta y palabras clave, guarda.
2. **Editar:** Clic en `✏️ Editar` en la fila correspondiente, modifica en el modal, actualiza.
3. **Eliminar:** Clic en `🗑️ Eliminar` — se pedirá confirmación antes de borrar.

**Consejo:** Las **palabras clave** son fundamentales para la calidad de las respuestas. Incluye variaciones: `domicilio, delivery, entrega, envío, llevar`.

---

## Cómo funcionan las Analíticas (`/admin/analytics`)

La página de analíticas muestra:

- **Total de preguntas** recibidas desde el inicio
- **Preguntas respondidas** (con coincidencia en la BD)
- **Sin respuesta** (puntuación por debajo del umbral)
- **Tasa de resolución** (porcentaje respondido correctamente)
- **Preguntas más frecuentes** (top 10 por frecuencia de aparición)
- **Últimas 10 conversaciones** con puntuación de similitud

Todas las conversaciones se guardan automáticamente en la tabla `chat_logs`.

---

## Cómo funciona el Modo Entrenamiento (`/admin/training`)

Cuando el chatbot **no puede responder** una pregunta (puntuación < umbral mínimo), la guarda automáticamente en la tabla `unanswered_questions`.

### Flujo de entrenamiento

1. Ve a `/admin/training`
2. Verás todas las preguntas que los clientes hicieron y el chatbot no supo responder
3. Para cada pregunta puedes:
   - **Reformularla** si la redacción original no es ideal
   - Escribir la **respuesta correcta**
   - Agregar las **palabras clave** relevantes
   - Hacer clic en **"Convertir a Base de Conocimiento"**
4. La pregunta desaparece del listado de entrenamiento y el chatbot ya sabrá responderla

Si la pregunta es irrelevante o spam, puedes usar **"Descartar"** para eliminarla.

---

## Entradas de ejemplo incluidas (18 en español)

| Tema | Ejemplo de pregunta |
|------|---------------------|
| Horarios | ¿Cuál es el horario de atención? |
| Ubicación | ¿Dónde están ubicados? |
| Domicilios | ¿Hacen domicilios? |
| Reservas | ¿Aceptan reservas? |
| Pagos | ¿Qué formas de pago aceptan? |
| Menú | ¿Qué tiene el menú? |
| Promociones | ¿Tienen promociones o descuentos? |
| Contacto | ¿Cómo puedo contactarlos? |
| Parqueadero | ¿Hay parqueadero? |
| Eventos | ¿Hacen eventos y celebraciones? |
| Wi-Fi | ¿Tienen Wi-Fi? |
| Tiempo de espera | ¿Cuánto tiempo demora el pedido? |
| Menú infantil | ¿Tienen menú infantil? |
| Pedido online | ¿Cómo hago un pedido en línea? |
| Para llevar | ¿Tienen productos para llevar? |
| Sin gluten | ¿Tienen opciones sin gluten? |
| Vegetariano | ¿Tienen opciones vegetarianas o veganas? |
| Devoluciones | ¿Cuál es la política de devoluciones? |

---

## Tecnologías utilizadas

| Componente | Tecnología |
|------------|------------|
| Backend | Python 3, Flask |
| Base de datos | SQLite (módulo `sqlite3` estándar) |
| Coincidencia | `difflib.SequenceMatcher` + Jaccard con extensión de raíz |
| Frontend | HTML5, CSS3 (variables CSS, animaciones), JavaScript ES6 (Fetch API) |
| Fuentes | Plus Jakarta Sans + JetBrains Mono (Google Fonts) |

No se requieren librerías de ML, claves de API ni conexión a Internet después de la primera carga de fuentes. Para uso completamente sin conexión, descarga las fuentes y sírvelas localmente.

---

## Personalización para tu negocio

1. Abre el **Panel de Administración** y elimina las entradas de ejemplo
2. Agrega tus propias preguntas frecuentes con sus respuestas
3. Ajusta `MATCH_THRESHOLD` en `chatbot_engine.py` si es necesario:
   - **Más bajo** (ej: 0.22) → más respuestas, posiblemente menos precisas
   - **Más alto** (ej: 0.40) → menos respuestas, pero solo las muy seguras
4. Cambia el nombre del negocio y los colores en `style.css` e `index.html`
