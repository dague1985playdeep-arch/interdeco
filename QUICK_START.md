# ⚡ Quick Start - Inter-Deco DM Manager

**Tiempo estimado: 5 minutos**

---

## 1️⃣ Preparar Credenciales

### Obtener Meta API Token
1. Ve a https://developers.facebook.com/
2. Messenger > Configuración > Token de acceso
3. Selecciona tu página
4. Copia el token (comienza con `EAAx...`)

### Obtener Instagram Business Account ID
```bash
# Reemplaza TOKEN con tu token
curl "https://graph.instagram.com/v21.0/me/ig_user_id?access_token=TOKEN"

# Respuesta:
{
  "ig_user_id": "17841400000000000"
}
```

### Obtener OpenAI API Key
1. Ve a https://platform.openai.com/api-keys
2. Crea nueva key
3. Copia el valor (comienza con `sk-`)

---

## 2️⃣ Instalación Rápida (Local)

```bash
# 1. Clonar
git clone https://github.com/dague1985playdeep-arch/interdeco.git
cd interdeco

# 2. Virtual environment
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# o
venv\Scripts\activate  # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar .env
cp .env.example .env

# Editar .env (importante!):
# META_ACCESS_TOKEN=tu_token_aqui
# INSTAGRAM_BUSINESS_ACCOUNT_ID=tu_id_aqui
# OPENAI_API_KEY=tu_key_aqui
# VERIFY_TOKEN=INTER_DECO_SECRET_2024

# 5. Inicializar BD
python init_db.py

# 6. Ejecutar
python main.py
```

✅ **Servidor corriendo en:** http://localhost:5000

---

## 3️⃣ Configurar Webhook en Meta (5 min)

1. **Ve a:** https://developers.facebook.com/
2. **Tu App > Messenger > Configuración**
3. **Agregar Webhook:**
   - URL: `http://localhost:5000/webhook` (o tu URL Render)
   - Token: `INTER_DECO_SECRET_2024`
   - Eventos: `messages`, `messaging_postbacks`
4. **Click "Verificar y guardar"**

Si ves ✅, ¡funcionó!

---

## 4️⃣ Prueba Local (sin Render)

### Usar ngrok para exponer puerto local

```bash
# Instalar ngrok
pip install ngrok

# En terminal 1 - Ejecutar app
python main.py

# En terminal 2 - Exponer
ngrok http 5000

# Verás algo como:
# Forwarding: https://abc123def456.ngrok.io

# Copiar esa URL a Facebook Developers webhook
```

### Enviar mensaje de prueba

```bash
# Desde tu Instagram, envía un DM a tu business account
# Debería:
# 1. Aparecer en el dashboard
# 2. Responder automáticamente con Fernanda
```

---

## 5️⃣ Deploy en Render (3 min)

### 5.1 Preparar

```bash
# Agregar a git
git add .
git commit -m "Deploy v2.0"
git push origin main
```

### 5.2 Render Dashboard

1. **Ir a:** https://render.com
2. **New > Web Service**
3. **Conectar GitHub** (autorizar)
4. **Seleccionar repositorio:** `interdeco`
5. **Configurar:**
   - Name: `interdeco-dm-manager`
   - Build: `pip install -r requirements.txt`
   - Start: `gunicorn main:app`

### 5.3 Variables de Entorno

En Render > Environment, agregar:

```
META_ACCESS_TOKEN=tu_token
INSTAGRAM_BUSINESS_ACCOUNT_ID=tu_id
OPENAI_API_KEY=tu_key
VERIFY_TOKEN=INTER_DECO_SECRET_2024
FLASK_ENV=production
```

### 5.4 Deploy

- Click **Deploy**
- Esperar 2-3 minutos
- Copiar URL pública: `https://interdeco-dm-manager.onrender.com`

---

## 6️⃣ Configurar Webhook en Meta (con Render)

1. **Meta Developers > Messenger > Configuración**
2. **Webhook URL:** `https://interdeco-dm-manager.onrender.com/webhook`
3. **Verificar y guardar**

---

## 7️⃣ Verificar que Funciona

### ✅ Checklist

- [ ] Servidor corre sin errores
- [ ] Dashboard accesible en `/`
- [ ] Meta verifica webhook
- [ ] Puedes ver clientes en `/api/customers`
- [ ] Envío un DM desde Instagram
- [ ] Aparece en dashboard
- [ ] Fernanda responde automáticamente

---

## 🐛 Troubleshooting Rápido

### ❌ "Connection refused" al iniciar
```bash
# Puerto 5000 en uso
lsof -i :5000  # Ver qué lo usa
kill -9 <PID>   # Matar proceso
```

### ❌ "ImportError: No module named 'flask'"
```bash
pip install -r requirements.txt
```

### ❌ "Token incorrecto" en webhook
- Verificar .env tiene VERIFY_TOKEN
- Debe coincidir con Meta Developers
- Sin espacios en blanco

### ❌ Mensaje de Meta no se recibe
```bash
# Revisar logs en Render:
# Dashboard > interdeco-dm-manager > Logs

# Si ves error 403 - Token expirado
# Generar nuevo en Facebook Developers
```

### ❌ IA no responde
- Verificar OPENAI_API_KEY es válido
- Verificar créditos en OpenAI
- Revisar logs de error

---

## 📊 Dashboard

Una vez corriendo, accede a:

```
http://localhost:5000
```

Verás:
- 📊 Estadísticas (conversaciones, clientes, urgentes)
- 👥 Lista de clientes activos
- 💬 Chat por cliente
- 📋 Historial de todos los mensajes

---

## 🔧 Operaciones Útiles

### Ver logs locales
```bash
# Terminal donde corre main.py
# Verás mensajes de debug en tiempo real
```

### Resetear BD
```bash
python init_db.py reset
```

### Crear datos de prueba
```bash
python init_db.py seed
```

### Probar API sin frontend
```bash
# Listar clientes
curl http://localhost:5000/api/customers

# Estadísticas
curl http://localhost:5000/api/conversations/stats

# Enviar mensaje manual
curl -X POST http://localhost:5000/api/send-message \
  -H "Content-Type: application/json" \
  -d '{"customer_id":"USER_ID","message":"Hola"}'
```

---

## 📚 Documentación Completa

Para más detalles, leer:

- **SETUP_GUIDE.md** - Guía detallada de configuración
- **IMPROVEMENTS.md** - Qué cambió y por qué
- **README.md** - Documentación general

---

## 🎉 ¡Listo!

Si completaste todos los pasos, tu sistema está funcionando. 

**Próximos pasos:**
- Personalizar prompt de Fernanda en `main.py` línea 105
- Agregar más lógica de IA según necesites
- Implementar notificaciones (email, WhatsApp, etc)
- Conectar con CRM de ventas

---

**Soporte:** 
- Issues en GitHub
- Logs en Render Dashboard
- Documentación Meta API: https://developers.facebook.com/docs/instagram-api

**Éxito!** 🚀
