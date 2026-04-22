import os
import sqlite3
import requests
from flask import Flask, request, jsonify
from openai import OpenAI
from datetime import datetime

app = Flask(__name__)

# --- CONFIGURACIÓN ---
# Las APIs las seguimos tomando de Render por seguridad
ACCESS_TOKEN = os.getenv('META_ACCESS_TOKEN')
INSTAGRAM_ACCOUNT_ID = os.getenv('INSTAGRAM_BUSINESS_ACCOUNT_ID')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# EL TOKEN DE VERIFICACIÓN (Fijo para que no falle en Meta)
MI_TOKEN_DE_META = "INTER_DECO_SECRET_2024"

client = OpenAI(api_key=OPENAI_API_KEY)

# --- BASE DE DATOS (Memoria de Fernanda) ---
def init_db():
    conn = sqlite3.connect('interdeco.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            role TEXT,
            content TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_history(user_id, role, content):
    conn = sqlite3.connect('interdeco.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO chat_history (user_id, role, content) VALUES (?, ?, ?)', (user_id, role, content))
    conn.commit()
    conn.close()

def get_history(user_id):
    conn = sqlite3.connect('interdeco.db')
    cursor = conn.cursor()
    cursor.execute('SELECT role, content FROM chat_history WHERE user_id = ? ORDER BY timestamp ASC LIMIT 10', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{"role": row[0], "content": row[1]} for row in rows]

# --- RUTAS ---

@app.route('/', methods=['GET'])
def home():
    return "<h1>Inter-Deco AI: Sistema Activo 🚀</h1>", 200

@app.route('/webhook', methods=['GET'])
def verify():
    # Capturamos los datos que envía Meta
    mode = request.args.get("hub.mode") or request.args.get("hub_mode")
    token = request.args.get("hub.verify_token") or request.args.get("hub_verify_token")
    challenge = request.args.get("hub.challenge") or request.args.get("hub_challenge")

    # Validación directa con el token fijo
    if mode == "subscribe" and token == MI_TOKEN_DE_META:
        print(f"✅ Webhook verificado con éxito. Challenge: {challenge}")
        return str(challenge), 200
    
    print(f"❌ Error: Token recibido ({token}) no coincide con {MI_TOKEN_DE_META}")
    return "Token de verificación inválido", 403

@app.route('/webhook', methods=['POST'])
def webhook_receiver():
    data = request.json
    if data.get("object") == "instagram":
        for entry in data.get("entry", []):
            for messaging_event in entry.get("messaging", []):
                sender_id = messaging_event["sender"]["id"]
                if "message" in messaging_event:
                    user_text = messaging_event["message"].get("text")
                    if user_text:
                        process_message(sender_id, user_text)
    return "EVENT_RECEIVED", 200

# --- LÓGICA DE RESPUESTA ---

def process_message(user_id, text):
    save_history(user_id, "user", text)
    history = get_history(user_id)
    
    instructions = ("Eres Fernanda, asistente de Inter-Deco. Experta en cortinas y diseño. "
                    "Amable, elegante y servicial. Ayuda al cliente a elegir la mejor opción.")
    
    messages = [{"role": "system", "content": instructions}] + history
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )
        ai_reply = response.choices[0].message.content
        save_history(user_id, "assistant", ai_reply)
        send_instagram_dm(user_id, ai_reply)
    except Exception as e:
        print(f"❌ Error OpenAI: {e}")

def send_instagram_dm(recipient_id, text):
    url = f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/messages"
    payload = {"recipient": {"id": recipient_id}, "message": {"text": text}}
    params = {"access_token": ACCESS_TOKEN}
    requests.post(url, json=payload, params=params)

if __name__ == "__main__":
    init_db()
    # Usamos el puerto dinámico de Render
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
