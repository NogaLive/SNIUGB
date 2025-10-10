import os
import requests
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from typing import List
from src.models.database_models import Animal

from dotenv import load_dotenv

load_dotenv()

def send_reset_code_by_email(to_email: str, code: str):
    message = Mail(
        from_email=os.getenv("FROM_EMAIL"),
        to_emails=to_email,
        subject='Tu Código de Recuperación de Contraseña SNIUGB',
        html_content=f'Hola,<br><br>Tu código para restablecer tu contraseña es: <strong>{code}</strong><br><br>Este código expirará en 10 minutos.'
    )
    try:
        sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
        response = sg.send(message)
        print(f"Correo de reseteo enviado a {to_email}, Status Code: {response.status_code}")
        return True
    except Exception as e:
        print(f"Error al enviar email de reseteo: {e}")
        return False

def send_reset_code_by_whatsapp(to_phone: str, code: str):
    whatsapp_token = os.getenv("WHATSAPP_TOKEN")
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    if not whatsapp_token or not phone_number_id:
        return False

    if to_phone.startswith('+'):
        formatted_to_phone = to_phone[1:]
    else:
        formatted_to_phone = to_phone
        
    api_url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
    headers = {"Authorization": f"Bearer {whatsapp_token}", "Content-Type": "application/json"}
    
    payload = {
        "messaging_product": "whatsapp", "to": formatted_to_phone, "type": "template",
        "template": {
            "name": "password_reset_code", "language": { "code": "es" },
            "components": [{"type": "body", "parameters": [{"type": "text", "text": code}]}]
        }
    }
    try:
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        print(f"Mensaje de reseteo de WhatsApp enviado a {formatted_to_phone}.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error al enviar mensaje de reseteo de WhatsApp: {e.response.text if e.response else e}")
        return False

def send_transfer_request_email(to_email: str, solicitante_nombre: str, codigo: str, animales: List[Animal]):
    """Envía un correo notificando una nueva solicitud con la lista de animales."""
    animal_list_html = "<ul>"
    for animal in animales:
        animal_list_html += f"<li><b>{animal.nombre}</b> (CUI: ...{animal.cui[-4:]})</li>"
    animal_list_html += "</ul>"
    
    message = Mail(
        from_email=os.getenv("FROM_EMAIL"),
        to_emails=to_email,
        subject='[SNIUGB] Tienes una nueva solicitud de transferencia',
        html_content=f'''
            Hola,<br><br>
            El usuario <strong>{solicitante_nombre}</strong> ha solicitado la transferencia de los siguientes animales:<br>
            {animal_list_html}
            <br>
            Para aprobar esta transferencia, ingresa el siguiente código en la plataforma:<br><br>
            <h1>{codigo}</h1>
            <br>
            Este código es secreto y solo debe ser usado por ti.<br>
            La solicitud expirará en 24 horas.
        '''
    )
    try:
        sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
        response = sg.send(message)
        print(f"Correo de transferencia enviado a {to_email}, Status Code: {response.status_code}")
        return True
    except Exception as e:
        print(f"Error al enviar email de transferencia: {e}")
        return False

def send_transfer_request_whatsapp(to_phone: str, solicitante_nombre: str, codigo: str, animales: List[Animal]):
    """Envía un mensaje de WhatsApp notificando una nueva solicitud de transferencia."""
    whatsapp_token = os.getenv("WHATSAPP_TOKEN")
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    if not whatsapp_token or not phone_number_id:
        return False

    if to_phone.startswith('+'):
        formatted_to_phone = to_phone[1:]
    else:
        formatted_to_phone = to_phone

    nombres_animales = ", ".join([animal.nombre for animal in animales])
    
    api_url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
    headers = {"Authorization": f"Bearer {whatsapp_token}", "Content-Type": "application/json"}
    
    payload = {
        "messaging_product": "whatsapp", "to": formatted_to_phone, "type": "template",
        "template": {
            "name": "transfer_request",
            "language": { "code": "es" },
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": solicitante_nombre},
                        {"type": "text", "text": str(len(animales))},
                        {"type": "text", "text": nombres_animales}
                    ]
                },
                {
                    "type": "button",
                    "sub_type": "quick_reply",
                    "index": "0",
                    "parameters": [{"type": "payload", "payload": codigo}]
                }
            ]
        }
    }
    try:
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        print(f"Notificación de transferencia de WhatsApp enviada a {formatted_to_phone}.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error al enviar notificación de transferencia de WhatsApp: {e.response.text if e.response else e}")
        return False
    
def send_new_support_ticket_notification(
    admin_email: str, 
    user_name: str, 
    user_dni: str, 
    ticket_category: str, 
    ticket_message: str
):
    """
    Envía un correo al administrador notificando un nuevo ticket de soporte.
    """
    message = Mail(
        from_email=os.getenv("FROM_EMAIL"),
        to_emails=admin_email,
        subject=f'[SNIUGB Soporte] Nuevo Ticket: {ticket_category}',
        html_content=f'''
            <h3>Se ha recibido una nueva solicitud de soporte.</h3>
            <p><strong>Usuario:</strong> {user_name} (DNI: {user_dni})</p>
            <p><strong>Categoría:</strong> {ticket_category}</p>
            <hr>
            <p><strong>Mensaje:</strong></p>
            <p>{ticket_message}</p>
        '''
    )
    try:
        sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
        response = sg.send(message)
        print(f"Notificación de soporte enviada a {admin_email}, Status Code: {response.status_code}")
        return True
    except Exception as e:
        print(f"Error al enviar email de soporte: {e}")
        return False