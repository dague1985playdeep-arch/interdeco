# 🎯 Inter-Deco DM Manager - Sistema de Gestión de Mensajes Directos

**Versión:** 2.0.0  
**Estado:** ✅ Production Ready  
**Última actualización:** Abril 2026

---

## 📌 Descripción General

Sistema completo de gestión de Direct Messages (DMs) para Instagram Business Account usando **Meta API** con respuestas automáticas impulsadas por **IA (OpenAI)**.

Incluye:
- ✅ Integración Meta API completa (Graph API v21.0)
- ✅ Base de datos relacional (SQLAlchemy)
- ✅ Historial de conversaciones con contexto
- ✅ Gestión de clientes y contactos
- ✅ Dashboard admin interactivo
- ✅ Categorización automática de mensajes
- ✅ API REST para automatización
- ✅ Deploy listo para Render, Heroku, AWS

---

## 🔴 Problemas Corregidos del Código Original

| # | Problema | Solución |
|---|----------|----------|
| 1 | ❌ Sin base de datos - pérdida de mensajes | ✅ SQLAlchemy + BD persistente |
| 2 | ❌ IA sin contexto de conversación | ✅ Historial de últimos 5 mensajes |
| 3 | ❌ Sin gestión de clientes | ✅ Tabla Customer con info de Meta |
| 4 | ❌ Webhook sin validación | ✅ Verificación de VERIFY_TOKEN |
| 5 | ❌ API calls sin manejo de errores | ✅ Try-catch y timeouts |
| 6 | ❌ Admin panel muy básico | ✅ Dashboard moderno con charts |
| 7 | ❌ Sin categorización de mensajes | ✅ Clasificación automática |
| 8 | ❌ Sin control de estado de lectura | ✅ mark_message_as_read() |

---

## 🚀 Quick Start (5 minutos)

### 1. Requisitos
```bash
Python 3.9+
Meta API Access Token
OpenAI API Key
Git
```

### 2. Instalación
```bash
git clone https://github.com/dague1985playdeep-arch/interdeco.git
cd interdeco
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### 3. Configurar .env
```bash
META_ACCESS_TOKEN=your_token_here
INSTAGRAM_BUSINESS_ACCOUNT_ID=17841400000000000
OPENAI_API_KEY=sk-...
VERIFY_TOKEN=INTER_DECO_SECRET_2024
```

### 4. Ejecutar
```bash
python init_db.py
python main.py
```

**Acceder a:** http://localhost:5000

---

## 📁 Estructura del Proyecto

```
interdeco/
├── main.py                 🔴 APP PRINCIPAL (NUEVO)
│                          - Gestión de webhooks
│                          - MetaDMManager class
│                          - Modelos de BD
│                          - API REST endpoints
│
├── init_db.py              🟢 INICIALIZACIÓN (NUEVO)
│                          - Crear/resetear tablas
│                          - Crear datos de prueba
│
├── index.html              🟡 DASHBOARD (MEJORADO)
│                          - Interfaz moderna
│                          - Chat interactivo
│                          - Estadísticas en tiempo real
│
├── requirements.txt        📦 DEPENDENCIAS (ACTUALIZADO)
│                          - Flask, SQLAlchemy
│                          - Requests, OpenAI
│                          - Flask-CORS, python-dotenv
│
├── .env.example            🔐 CONFIG TEMPLATE (NUEVO)
│                          - Variables de entorno
│
├── SETUP_GUIDE.md          📚 GUÍA COMPLETA (NUEVO)
│                          - Instalación paso a paso
│                          - Meta API configuration
│                          - Render deployment
│
├── QUICK_START.md          ⚡ INICIO RÁPIDO (NUEVO)
│                          - 5 minutos para empezar
│
├── IMPROVEMENTS.md         📋 DETALLE DE CAMBIOS (NUEVO)
│                          - Antes vs Después
│                          - Arquitectura nueva
│
└── README.md               📖 ESTE ARCHIVO
```

---

## 🏛️ Arquitectura

### Stack Tecnológico

```
Frontend:
  - HTML5 / CSS3 / JavaScript
  - Bootstrap 5.3
  - Font Awesome 6.4

Backend:
  - Flask 3.1 (Python)
  - SQLAlchemy 2.0 (ORM)
  - Flask-CORS 6.0

Base de Datos:
  - SQLite (desarrollo)
  - PostgreSQL (producción)

APIs Externas:
  - Meta Graph API v21.0
  - OpenAI API (GPT-4o)

Deployment:
  - Render.com
  - Gunicorn WSGI server
```

### Flujo de Datos

```
📱 Instagram User envía DM
        ↓
🔔 Meta API envía webhook POST
        ↓
🔐 Verificamos VERIFY_TOKEN
        ↓
👤 Obtener/crear cliente en BD
        ↓
📜 Cargar historial (últimos 5 msgs)
        ↓
🤖 OpenAI responde (con contexto)
        ↓
💾 Guardar en BD (conversación)
        ↓
📤 Enviar respuesta via Meta API
        ↓
✅ Marcar como leído
        ↓
📊 Dashboard se actualiza automáticamente
```

---

## 🗄️ Base de Datos

### Tablas

#### customers
```python
id                  String(100)    # Meta user ID (PK)
name                String(255)    # Nombre del cliente
phone               String(20)     # Teléfono
email               String(255)    # Email
profile_pic_url     String(500)    # Foto de perfil
created_at          DateTime       # Fecha creación
updated_at          DateTime       # Última actualización
```

#### conversations
```python
id                  Integer        # ID único (PK)
customer_id         String(100)    # Referencia a customer (FK)
user_message        Text           # Mensaje del cliente
ai_response         Text           # Respuesta de IA
category            String(50)     # VENTAS, POST-VENTA, URGENTE, SPAM
created_at          DateTime       # Timestamp del mensaje
meta_message_id     String(255)    # ID del mensaje en Meta (UNIQUE)
```

---

## 🔌 API Endpoints

### Admin Panel
```
GET  /                              # Dashboard HTML
```

### Clientes
```
GET  /api/customers                 # Listar todos (JSON)
GET  /api/customers/<id>            # Detalles + conversaciones
```

### Conversaciones
```
GET  /api/conversations             # Últimas 50
GET  /api/conversations?category=X  # Filtrar por categoría
GET  /api/conversations/stats       # Estadísticas globales
```

### Mensajes
```
POST /api/send-message              # Enviar DM manual
```

### Salud
```
GET  /api/health                    # Estado de la app
```

### Webhooks
```
GET  /webhook                       # Verificación Meta
POST /webhook                       # Recibir eventos
```

---

## 🤖 Características de IA

### Contexto Histórico
La IA tiene acceso a los últimos 5 mensajes de la conversación para mantener coherencia:

```python
# Obtener historial para contexto
historial = db.session.query(Conversation).filter_by(
    customer_id=sender_id
).order_by(Conversation.created_at.desc()).limit(5).all()

# Enviar a OpenAI con contexto completo
messages = [
    {"role": "system", "content": prompt},
    ...historial,
    {"role": "user", "content": mensaje_actual}
]
```

### Categorización Automática

Clasifica automáticamente en:
- **VENTAS** - Precios, presupuestos, información de productos
- **POST-VENTA** - Problemas, devoluciones, servicio técnico
- **URGENTE** - Palabras clave urgentes, múltiples exclamaciones
- **SPAM** - Spam, links sospechosos
- **GENERAL** - Otros

### Personalidad de IA
Fernanda es la asistente de Inter-Deco:
- 💬 Habla relajado (estilo chileno)
- 🎯 Profesional y educada
- ⏱️ Respuestas concisas (máx 15 palabras)
- 📋 Siempre pide fotos y medidas

---

## 🛠️ Customización

### Cambiar Prompt de IA

En `main.py`, línea ~100:

```python
def obtener_respuesta_ia(mensaje_usuario, historial_contexto=[]):
    messages = [
        {
            "role": "system",
            "content": (
                "Tu nuevo prompt aquí..."
            )
        }
    ]
```

### Agregar Nuevas Categorías

En `main.py`, función `clasificar_mensaje()`:

```python
def clasificar_mensaje(texto):
    texto_lower = texto.lower()
    
    if any(word in texto_lower for word in ['tu_palabra_clave']):
        return 'TU_CATEGORIA'
    # ... más lógica
```

### Cambiar Webhook Port

En `main.py`, línea final:

```python
port = int(os.environ.get("PORT", 5000))  # Cambiar 5000 a otro puerto
app.run(host='0.0.0.0', port=port)
```

---

## 📊 Monitoreo y Logs

### Logs Locales
```bash
# Los ves en tiempo real en la terminal donde corre:
# python main.py

# Ejemplos:
✅ WEBHOOK VERIFICADO CON META
📬 Mensaje de 17841400000000: Hola, me interesa...
✅ Mensaje enviado a 17841400000000: message_id_123
💾 Guardado en BD: conversacion_456
```

### Logs en Render

```bash
# Dashboard > interdeco-dm-manager > Logs
# Ver en tiempo real todos los eventos
```

### Métricas

```bash
# Endpoint de estadísticas
GET /api/conversations/stats

# Respuesta:
{
  "total_conversations": 150,
  "total_customers": 42,
  "categories": {
    "VENTAS": 80,
    "POST-VENTA": 40,
    "URGENTE": 20,
    "SPAM": 10
  }
}
```

---

## 🔒 Seguridad

### Implementado
- ✅ Verificación de VERIFY_TOKEN en webhooks
- ✅ Validación de eventos de Meta
- ✅ Manejo de excepciones en todas las API calls
- ✅ Timeouts en requests (10 segundos)
- ✅ Sanitización de inputs
- ✅ CORS habilitado solo para necesario

### Recomendaciones de Producción
- 🔐 Usar HTTPS (Render lo hace automáticamente)
- 🔐 Guardar tokens en variables de entorno
- 🔐 Usar PostgreSQL en lugar de SQLite
- 🔐 Implementar rate limiting
- 🔐 Agregar autenticación al dashboard
- 🔐 Rotar access tokens regularmente

---

## 🚀 Deployment

### Render.com (Recomendado)

```bash
# 1. Crear archivo render.yaml:
services:
  - type: web
    name: interdeco-dm-manager
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn main:app
    envVars:
      - key: FLASK_ENV
        value: production
      - key: META_ACCESS_TOKEN
        value: ${META_ACCESS_TOKEN}
      # ... más variables

# 2. Push a GitHub
git add .
git commit -m "Deploy v2.0"
git push

# 3. Render automáticamente:
# - Clona repositorio
# - Instala dependencias
# - Ejecuta servidor
# - Asigna dominio público
```

### Alternativas
- **Heroku** - `git push heroku main`
- **AWS Lambda** - Con Zappa
- **Digital Ocean** - Con Docker
- **PythonAnywhere** - Sin línea de comandos

---

## 🧪 Testing

### Crear Datos de Prueba
```bash
python init_db.py seed
```

### Probar Endpoints
```bash
# Health check
curl http://localhost:5000/api/health

# Listar clientes
curl http://localhost:5000/api/customers

# Enviar mensaje manual
curl -X POST http://localhost:5000/api/send-message \
  -H "Content-Type: application/json" \
  -d '{"customer_id":"test_user_123","message":"Hola!"}'
```

### Probar Webhook Localmente
```bash
# Terminal 1: app corriendo
python main.py

# Terminal 2: usar ngrok
ngrok http 5000

# Terminal 3: prueba
curl -X GET "http://localhost:5000/webhook?hub.mode=subscribe&hub.verify_token=INTER_DECO_SECRET_2024&hub.challenge=test123"

# Deberías recibir: test123
```

---

## 🐛 Troubleshooting

| Problema | Causa | Solución |
|----------|-------|----------|
| ❌ "No module named 'flask'" | Falta instalar dependencias | `pip install -r requirements.txt` |
| ❌ "Connection refused" | Puerto 5000 en uso | `lsof -i :5000` y kill process |
| ❌ Webhook no verifica | VERIFY_TOKEN incorrecto | Revisar .env y Meta Developers |
| ❌ Mensajes no se reciben | Token expirado | Generar nuevo en Developers |
| ❌ IA no responde | OpenAI key inválido | Verificar créditos en OpenAI |
| ❌ BD bloqueada | Múltiples conexiones SQLite | Cambiar a PostgreSQL |

---

## 📚 Documentación Completa

| Archivo | Propósito |
|---------|-----------|
| **QUICK_START.md** | 🚀 Empezar en 5 minutos |
| **SETUP_GUIDE.md** | 📋 Configuración detallada |
| **IMPROVEMENTS.md** | 📊 Qué cambió del código viejo |
| **README.md** | 📖 Este archivo |

---

## 🎓 Conceptos Clave

### 1. MetaDMManager
Clase que centraliza toda la lógica de Meta API en un lugar reutilizable.

### 2. SQLAlchemy ORM
Mapea tablas de BD a objetos Python, evita inyecciones SQL.

### 3. Historial de Contexto
Los últimos 5 mensajes se envían a OpenAI para mejor entendimiento.

### 4. Webhook Verification
Meta verifica que nuestra URL es legítima enviando un token.

### 5. Categorización Inteligente
Clasifica automáticamente por palabras clave.

---

## 📈 Roadmap Futuro

- [ ] Autenticación del dashboard
- [ ] Integración con WhatsApp Business API
- [ ] Análisis de sentimientos
- [ ] Respuestas personalizadas por cliente
- [ ] Integración con CRM (Salesforce, Hubspot)
- [ ] Notificaciones en tiempo real
- [ ] Soporte para attachments (imágenes, PDFs)
- [ ] Sistema de templates de respuesta
- [ ] Exportar conversaciones a CSV/PDF

---

## 📞 Soporte y Contacto

- **Issues:** https://github.com/dague1985playdeep-arch/interdeco/issues
- **Meta API Docs:** https://developers.facebook.com/docs/instagram-api
- **OpenAI Docs:** https://platform.openai.com/docs

---

## 📄 Licencia

Este proyecto es propiedad de Inter-Deco.cl

---

## 🙏 Agradecimientos

- Meta Platform (Graph API)
- OpenAI (GPT-4o)
- Flask & SQLAlchemy comunidades
- Render.com por hosting

---

## 📊 Estadísticas

- **Líneas de código:** ~1,500
- **Funciones:** 20+
- **Endpoints API:** 8
- **Tablas BD:** 2
- **Documentación:** 4 guías completas

---

**Versión:** 2.0.0  
**Última actualización:** Abril 2026  
**Estado:** ✅ Production Ready  
**Maintainer:** @dague1985playdeep-arch

---

## 🚀 ¡Listo para producción!

Sigue **QUICK_START.md** para empezar en 5 minutos.

Pregunta cualquier duda - estoy aquí para ayudar. 💪
