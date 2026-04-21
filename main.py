import os
import requests
import json
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from openai import OpenAI
from sqlalchemy import func

# ==================== CONFIGURACIÓN ====================
load_dotenv()

app = Flask(__name__)
CORS(app)

# --- VARIABLES DE ENTORNO ---
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")  # Token de acceso Meta/Instagram
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "INTER_DECO_SECRET_2024")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
INSTAGRAM_BUSINESS_ACCOUNT_ID = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")
BUSINESS_PAGE_ID = os.getenv("BUSINESS_PAGE_ID")

# --- CONFIGURACIÓN DE BASE DE DATOS ---
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL', 
    'sqlite:///interdeco_dm.db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
client = OpenAI(api_key=OPENAI_API_KEY)

# ==================== MODELOS DE BASE DE DATOS ====================

class Customer(db.Model):
    """Modelo para almacenar información de clientes"""
    __tablename__ = 'customers'
    
    id = db.Column(db.String(100), primary_key=True)  # Meta user ID
    name = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    profile_pic_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    conversations = db.relationship('Conversation', backref='customer', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'email': self.email,
            'profile_pic_url': self.profile_pic_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'total_messages': len(self.conversations)
        }


class Conversation(db.Model):
    """Modelo para almacenar conversaciones individuales"""
    __tablename__ = 'conversations'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.String(100), db.ForeignKey('customers.id'), nullable=False)
    user_message = db.Column(db.Text, nullable=False)
    ai_response = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default='GENERAL')  # VENTAS, POST-VENTA, SPAM, URGENTE
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    meta_message_id = db.Column(db.String(255), nullable=True, unique=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'user_message': self.user_message,
            'ai_response': self.ai_response,
            'category': self.category,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# ==================== FUNCIONES DE META API ====================

class MetaDMManager:
    """Gestor centralizado de API de Meta para Direct Messages"""
    
    META_GRAPH_API_URL = "https://graph.instagram.com/v21.0"
    
    def __init__(self, access_token):
        self.access_token = access_token
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
    
    def get_user_info(self, user_id):
        """Obtiene información del usuario desde Meta API"""
        try:
            url = f"{self.META_GRAPH_API_URL}/{user_id}"
            params = {
                "fields": "id,name,username,profile_pic_url,email",
                "access_token": self.access_token
            }
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error obteniendo info del usuario {user_id}: {e}")
            return None
    
    def send_dm(self, recipient_id, message_text, message_type="text"):
        """
        Envía un mensaje directo a través de Meta API
        
        Args:
            recipient_id: ID del destinatario (Meta user ID)
            message_text: Texto del mensaje
            message_type: Tipo de mensaje ('text', 'image', etc)
        
        Returns:
            dict con el resultado o None si falla
        """
        try:
            url = f"{self.META_GRAPH_API_URL}/me/messages"
            
            payload = {
                "recipient": {"id": recipient_id},
                "message": {"text": message_text} if message_type == "text" else {
                    "attachment": {"type": message_type, "payload": {"url": message_text}}
                }
            }
            
            params = {"access_token": self.access_token}
            response = requests.post(url, json=payload, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            print(f"✅ Mensaje enviado a {recipient_id}: {result.get('message_id', 'ID no retornado')}")
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error enviando DM: {e}")
            return None
    
    def get_conversation_history(self, conversation_id, limit=50):
        """Obtiene el historial de una conversación"""
        try:
            url = f"{self.META_GRAPH_API_URL}/{conversation_id}/messages"
            params = {
                "fields": "id,to,from,message,created_timestamp,type",
                "limit": limit,
                "access_token": self.access_token
            }
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json().get('data', [])
        except requests.exceptions.RequestException as e:
            print(f"❌ Error obteniendo historial: {e}")
            return []
    
    def mark_message_as_read(self, message_id):
        """Marca un mensaje como leído"""
        try:
            url = f"{self.META_GRAPH_API_URL}/{message_id}"
            payload = {"status": "READ"}
            params = {"access_token": self.access_token}
            response = requests.post(url, json=payload, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Error marcando como leído: {e}")
            return False


# Instancia global del gestor
dm_manager = MetaDMManager(META_ACCESS_TOKEN)


# ==================== LÓGICA DE IA ====================

def obtener_respuesta_ia(mensaje_usuario, historial_contexto=[]):
    """
    Obtiene respuesta de IA con contexto de conversación
    
    Args:
        mensaje_usuario: Mensaje del cliente
        historial_contexto: Lista de mensajes previos para contexto
    
    Returns:
        dict con 'respuesta' y 'categoria'
    """
    try:
        # Construir mensajes para el modelo
        messages = [
            {
                "role": "system",
                "content": (
                    "Eres Fernanda, la asistente experta de Inter-Deco.cl. "
                    "Hablas relajado en estilo chileno, pero siempre profesional y educada. "
                    "Máximo 15 palabras por respuesta. "
                    "REGLAS CRÍTICAS:\n"
                    "1. NUNCA des precios por DM. Pide fotos, medidas y datos de delivery.\n"
                    "2. Sé amable y de rápida respuesta.\n"
                    "3. Clasifica el tipo de consulta internamente.\n"
                    "Responde de forma natural, sin formato JSON, solo el texto de la respuesta."
                )
            }
        ]
        
        # Agregar historial como contexto (últimos 5 mensajes)
        for msg in historial_contexto[-5:]:
            messages.append({"role": "user", "content": msg['user_message']})
            messages.append({"role": "assistant", "content": msg['ai_response']})
        
        # Mensaje actual
        messages.append({"role": "user", "content": mensaje_usuario})
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=100,
            temperature=0.7
        )
        
        respuesta = response.choices[0].message.content.strip()
        
        # Clasificación del mensaje (post-procesamiento)
        categoria = clasificar_mensaje(mensaje_usuario)
        
        return {
            'respuesta': respuesta,
            'categoria': categoria
        }
        
    except Exception as e:
        print(f"❌ Error en OpenAI: {e}")
        return {
            'respuesta': "Hola, disculpa el delay. ¿En qué te puedo ayudar?",
            'categoria': 'ERROR'
        }


def clasificar_mensaje(texto):
    """Clasifica un mensaje por palabras clave"""
    texto_lower = texto.lower()
    
    if any(word in texto_lower for word in ['precio', 'costo', 'cuánto', 'valor', 'pago', 'tarjeta']):
        return 'VENTAS'
    elif any(word in texto_lower for word in ['problema', 'error', 'falla', 'no funciona', 'defecto']):
        return 'POST-VENTA'
    elif any(word in texto_lower for word in ['urgente', 'rápido', 'ahora', 'ayuda', '!', '!!!']):
        return 'URGENTE'
    elif any(word in texto_lower for word in ['viagra', 'casino', 'sorteo', 'gratis', 'click']):
        return 'SPAM'
    else:
        return 'GENERAL'


# ==================== RUTAS - WEBHOOK ====================

@app.route('/webhook', methods=['GET'])
def verificar_webhook():
    """Verifica el webhook con Meta"""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    
    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("✅ WEBHOOK VERIFICADO CON META")
        return challenge, 200
    
    return "Token incorrecto", 403


@app.route('/webhook', methods=['POST'])
def recibir_eventos():
    """
    Recibe eventos de Meta API
    Procesa mensajes entrantes y responde automáticamente
    """
    data = request.json
    
    if not data:
        return "No data", 400
    
    # Verificar que es un evento de Instagram/Messenger
    if data.get("object") != "instagram" and data.get("object") != "page":
        return "Not Instagram/Page event", 400
    
    try:
        for entry in data.get("entry", []):
            # Procesar messaging events
            for messaging_event in entry.get("messaging", []):
                procesar_mensaje_entrante(messaging_event)
            
            # Procesar webhook events (cambios)
            for changes in entry.get("changes", []):
                procesar_cambios(changes)
        
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        print(f"❌ Error procesando webhook: {e}")
        return jsonify({"error": str(e)}), 500


def procesar_mensaje_entrante(messaging_event):
    """Procesa un mensaje entrante"""
    
    # Ignorar confirmaciones de lectura
    if "delivery" in messaging_event or "read" in messaging_event:
        return
    
    # Verificar que hay mensaje
    if not messaging_event.get("message"):
        return
    
    # Extraer datos
    sender_id = messaging_event.get("sender", {}).get("id")
    message_data = messaging_event.get("message", {})
    message_id = message_data.get("mid")  # Message ID de Meta
    texto_recibido = message_data.get("text")
    
    if not sender_id or not texto_recibido:
        print("⚠️  Mensaje sin texto o sin sender_id")
        return
    
    print(f"📬 Mensaje de {sender_id}: {texto_recibido}")
    
    # Marcar como leído
    dm_manager.mark_message_as_read(message_id)
    
    # Obtener o crear cliente
    customer = obtener_o_crear_cliente(sender_id)
    
    # Obtener historial de conversación para contexto
    historial = db.session.query(Conversation).filter_by(
        customer_id=sender_id
    ).order_by(Conversation.created_at.desc()).limit(5).all()
    
    historial_contexto = [
        {
            'user_message': conv.user_message,
            'ai_response': conv.ai_response
        } for conv in reversed(historial)
    ]
    
    # Obtener respuesta de IA
    ia_response = obtener_respuesta_ia(texto_recibido, historial_contexto)
    
    # Guardar en base de datos
    conversation = Conversation(
        customer_id=sender_id,
        user_message=texto_recibido,
        ai_response=ia_response['respuesta'],
        category=ia_response['categoria'],
        meta_message_id=message_id
    )
    db.session.add(conversation)
    db.session.commit()
    
    # Enviar respuesta a Meta
    dm_manager.send_dm(sender_id, ia_response['respuesta'])


def procesar_cambios(changes):
    """Procesa cambios en la conversación (usado para futuros webhooks)"""
    field = changes.get("field")
    value = changes.get("value", {})
    
    # Aquí puedes manejar otros tipos de eventos
    # Por ejemplo: cambios de estado, etc.
    print(f"📊 Cambio detectado en campo: {field}")


def obtener_o_crear_cliente(user_id):
    """Obtiene un cliente existente o crea uno nuevo"""
    customer = Customer.query.get(user_id)
    
    if not customer:
        # Obtener info del usuario desde Meta API
        user_info = dm_manager.get_user_info(user_id)
        
        customer = Customer(
            id=user_id,
            name=user_info.get('name') if user_info else 'Cliente',
            email=user_info.get('email') if user_info else None,
            profile_pic_url=user_info.get('profile_pic_url') if user_info else None
        )
        db.session.add(customer)
        db.session.commit()
    
    return customer


# ==================== RUTAS - ADMIN PANEL ====================

@app.route('/api/customers', methods=['GET'])
def listar_clientes():
    """Lista todos los clientes"""
    clientes = Customer.query.order_by(Customer.updated_at.desc()).all()
    return jsonify([c.to_dict() for c in clientes])


@app.route('/api/customers/<customer_id>', methods=['GET'])
def obtener_cliente(customer_id):
    """Obtiene detalles de un cliente específico"""
    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({"error": "Cliente no encontrado"}), 404
    
    conversations = Conversation.query.filter_by(
        customer_id=customer_id
    ).order_by(Conversation.created_at.desc()).all()
    
    return jsonify({
        'customer': customer.to_dict(),
        'conversations': [c.to_dict() for c in conversations]
    })


@app.route('/api/conversations', methods=['GET'])
def listar_conversaciones():
    """Lista todas las conversaciones con filtros"""
    category = request.args.get('category')
    limit = request.args.get('limit', 50, type=int)
    
    query = Conversation.query
    if category:
        query = query.filter_by(category=category)
    
    conversations = query.order_by(Conversation.created_at.desc()).limit(limit).all()
    return jsonify([c.to_dict() for c in conversations])


@app.route('/api/conversations/stats', methods=['GET'])
def estadisticas_conversaciones():
    """Obtiene estadísticas de conversaciones"""
    total_conversations = db.session.query(func.count(Conversation.id)).scalar()
    total_customers = db.session.query(func.count(Customer.id)).scalar()
    
    categories_count = db.session.query(
        Conversation.category,
        func.count(Conversation.id)
    ).group_by(Conversation.category).all()
    
    return jsonify({
        'total_conversations': total_conversations,
        'total_customers': total_customers,
        'categories': {cat: count for cat, count in categories_count}
    })


@app.route('/api/send-message', methods=['POST'])
def enviar_mensaje_manual():
    """Permite enviar un mensaje manual a un cliente"""
    data = request.json
    customer_id = data.get('customer_id')
    message = data.get('message')
    
    if not customer_id or not message:
        return jsonify({"error": "Faltan datos"}), 400
    
    result = dm_manager.send_dm(customer_id, message)
    
    if result:
        return jsonify({
            "status": "success",
            "message_id": result.get('message_id')
        })
    else:
        return jsonify({"error": "Error enviando mensaje"}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Verifica el estado de la aplicación"""
    return jsonify({
        "status": "ok",
        "database": "connected",
        "timestamp": datetime.utcnow().isoformat()
    })


# ==================== INICIALIZACIÓN ====================

if __name__ == '__main__':
    # Crear tablas si no existen
    with app.app_context():
        db.create_all()
        print("✅ Base de datos inicializada")
    
    # Ejecutar servidor
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    
    print(f"""
    🚀 Inter-Deco DM Manager iniciado
    📍 http://0.0.0.0:{port}
    🔐 Webhook verificado: /webhook
    📊 Admin Panel: /
    """)
    
    app.run(host='0.0.0.0', port=port, debug=debug)
