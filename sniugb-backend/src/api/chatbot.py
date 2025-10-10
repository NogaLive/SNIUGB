from fastapi import APIRouter, Request, HTTPException
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

# --- Configuración ---
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
API_VERSION = "v19.0" # Usa una versión reciente de la API de Graph
API_URL = f"https://graph.facebook.com/{API_VERSION}/{WHATSAPP_PHONE_NUMBER_ID}/messages"

chatbot_router = APIRouter(prefix="/whatsapp", tags=["Chatbot WhatsApp"])

# Uso de una "memoria" temporal
user_states = {}

# --- Función para enviar mensajes  ---
def send_whatsapp_message(to: str, text: str):
    """
    Envía un mensaje de texto simple a un número de WhatsApp.
    """
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        print(f"Mensaje enviado a {to} exitosamente.")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error al enviar mensaje de WhatsApp: {e.response.text if e.response else e}")
        return None

# --- Lógica Principal del Chatbot ---
async def handle_message(message):
    sender_id = message['from']
    text = message['text']['body'].strip()
    state = user_states.get(sender_id, {'stage': 'inicio'})

    if state['stage'] == 'inicio' and text == '1':
        send_whatsapp_message(sender_id, "Por favor, ingresa tu número de DNI:")
        user_states[sender_id] = {'stage': 'awaiting_login_dni'}
        
    elif state['stage'] == 'awaiting_login_dni':
        dni = text
        send_whatsapp_message(sender_id, "Gracias. Ahora, ingresa tu contraseña:")
        user_states[sender_id] = {'stage': 'awaiting_login_password', 'dni': dni}
        
    elif state['stage'] == 'awaiting_login_password':
        password = text
        dni = state['dni']
        try:
            response = requests.post("http://127.0.0.1:8000/api/auth/login", data={'username': dni, 'password': password})
            response.raise_for_status()
            token_data = response.json()
            user_states[sender_id] = {'stage': 'authenticated', 'token': token_data['access_token']}
            send_whatsapp_message(sender_id, f"✅ ¡Bienvenido! Sesión iniciada.")
            send_whatsapp_message(sender_id, "Menú Principal:\n1. Consultar animal por QR\n2. Registrar nuevo animal")
        except requests.exceptions.HTTPError:
            send_whatsapp_message(sender_id, "❌ DNI o contraseña incorrectos. Por favor, intenta de nuevo.")
            user_states[sender_id] = {'stage': 'inicio'}
            send_whatsapp_message(sender_id, "Menú:\n1. Iniciar Sesión\n2. Registrarse")
    
    else:
        user_states[sender_id] = {'stage': 'inicio'}
        send_whatsapp_message(sender_id, "Bienvenido al Chatbot de SNIUGB. Responde con un número para elegir una opción:")
        send_whatsapp_message(sender_id, "1. Iniciar Sesión\n2. Registrarse")


# --- ENDPOINTS DEL WEBHOOK ---

@chatbot_router.get("/webhook")
async def verify_webhook(request: Request):
    """Verifica el webhook con Meta."""
    if "hub.mode" in request.query_params and "hub.verify_token" in request.query_params:
        mode = request.query_params.get("hub.mode")
        token = request.query_params.get("hub.verify_token")
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return int(request.query_params.get("hub.challenge"))
    raise HTTPException(status_code=403, detail="Verification token is not valid.")

@chatbot_router.post("/webhook")
async def webhook(request: Request):
    """Recibe los mensajes de WhatsApp y los procesa."""
    data = await request.json()
    print("Payload recibido de WhatsApp:", json.dumps(data, indent=2))

    try:
        if data['entry'][0]['changes'][0]['value']['messages']:
            message = data['entry'][0]['changes'][0]['value']['messages'][0]
            await handle_message(message)
    except (KeyError, IndexError, TypeError):
        print("Payload recibido no es un mensaje de usuario, ignorando.")
        pass

    return {"status": "ok"}