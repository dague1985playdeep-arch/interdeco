import os
import sqlite3
import requests
from flask import Flask, request, jsonify
from openai import OpenAI
from datetime import datetime

app = Flask(__name__)

# --- CONFIGURACIÓN ---
# Estos valores se configuran en el panel 'Environment' de Render
ACCESS_TOKEN = os.getenv('META_ACCESS_TOKEN')
VERIFY_TOKEN = os.getenv('VERIFY_TOKEN')
INSTAGRAM_ACCOUNT_ID = os.getenv('INSTAGRAM_BUSINESS_ACCOUNT_ID')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

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
    # Esta ruta evita el error 404 al entrar a la URL principal
    return "<h1>Inter-Deco AI: Sistema Activo 🚀</h1>", 200

@app.route('/webhook', methods=['GET'])
def verify():
    # Validación requerida por Meta Developers
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("✅ Webhook verificado correctamente.")
        return challenge, 200
    return "Error de validación", 403

@app.route('/webhook', methods=['GET'])
def verify():
    # Forzamos a que ignore cualquier error de formato de Meta
    token_sent = request.args.get("hub.verify_token")
    if token_sent == os.getenv('VERIFY_TOKEN'):
        return request.args.get("hub.challenge")
    return "Token incorrecto", 403
# --- LÓGICA DE RESPUESTA ---

def process_message(user_id, text):
    # Guardar lo que dijo el usuario
    save_history(user_id, "user", text)
    
    # Obtener historial para darle contexto a la IA
    history = get_history(user_id)
    
    # Fernanda genera respuesta
    instructions = ("Eres Fernanda, asistente de Inter-Deco. Experta en cortinas y diseño. "
                    "Amable, elegante y servicial. Siempre intenta ayudar al cliente a elegir "
                    "la mejor opción para sus ventanas.")
    
    messages = [{"role": "system", "content": instructions}] + history
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )
        ai_reply = response.choices[0].message.content
        
        # Guardar y enviar
        save_history(user_id, "assistant", ai_reply)
        send_instagram_dm(user_id, ai_reply)
    except Exception as e:
        print(f"❌ Error en OpenAI: {e}")

def send_instagram_dm(recipient_id, text):
    url = f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/messages"
    payload = {"recipient": {"id": recipient_id}, "message": {"text": text}}
    params = {"access_token": ACCESS_TOKEN}
    requests.post(url, json=payload, params=params)

if __name__ == "__main__":
    init_db()
    app.run(host='0.0.0.0', port=5000)
