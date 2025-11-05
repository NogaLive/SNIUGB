import os
import requests
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from typing import List
from src.models.database_models import Animal
from dotenv import load_dotenv

load_dotenv()

def send_reset_code_by_email(to_email: str, code: str) -> bool:
    api_key = os.getenv("SENDGRID_API_KEY")
    from_email = os.getenv("FROM_EMAIL")
    if not api_key or not from_email:
        print("Falta SENDGRID_API_KEY o FROM_EMAIL")
        return False

    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject='Tu Código de Recuperación de Contraseña SNIUGB',
        html_content=(
            'Hola,<br><br>'
            f'Tu código para restablecer tu contraseña es: <strong>{code}</strong><br><br>'
            'Este código expirará en 10 minutos.'
        )
    )
    try:
        sg = SendGridAPIClient(api_key)
        resp = sg.send(message)
        ok = resp.status_code in (200, 202)
        if not ok:
            print(f"SendGrid no aceptó el envío: {resp.status_code} {getattr(resp, 'body', '')}")
        else:
            print(f"Correo de reseteo aceptado por SendGrid ({resp.status_code}) para {to_email}")
        return ok
    except Exception as e:
        print(f"Error al enviar email de reseteo: {e}")
        return False


def send_reset_code_by_whatsapp(to_phone: str, code: str) -> bool:
    # Acepta ambos nombres de variable para compatibilidad
    whatsapp_token = os.getenv("WHATSAPP_TOKEN") or os.getenv("WHATSAPP_API_TOKEN")
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    if not whatsapp_token or not phone_number_id:
        print("Falta WHATSAPP_TOKEN/WHATSAPP_API_TOKEN o WHATSAPP_PHONE_NUMBER_ID")
        return False

    formatted_to_phone = to_phone[1:] if to_phone.startswith('+') else to_phone
    api_url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
    headers = {"Authorization": f"Bearer {whatsapp_token}", "Content-Type": "application/json"}

    payload = {
        "messaging_product": "whatsapp",
        "to": formatted_to_phone,
        "type": "template",
        "template": {
            "name": "password_reset_code",
            "language": { "code": "es" },
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": code}
                    ]
                }
            ]
        }
    }
    try:
        r = requests.post(api_url, headers=headers, json=payload)
        r.raise_for_status()
        print(f"WhatsApp reset enviado a {formatted_to_phone}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error WhatsApp reset: {e.response.text if e.response else e}")
        return False


def send_transfer_request_email(to_email: str, solicitante_nombre: str, codigo: str, animales: List[Animal]) -> bool:
    animal_list_html = "<ul>"
    for animal in animales:
        cui_tail = animal.cui[-4:] if getattr(animal, "cui", None) else "----"
        animal_list_html += f"<li><b>{animal.nombre}</b> (CUI: ...{cui_tail})</li>"
    animal_list_html += "</ul>"

    api_key = os.getenv("SENDGRID_API_KEY")
    from_email = os.getenv("FROM_EMAIL")
    if not api_key or not from_email:
        print("Falta SENDGRID_API_KEY o FROM_EMAIL")
        return False

    message = Mail(
        from_email=from_email,
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
        sg = SendGridAPIClient(api_key)
        resp = sg.send(message)
        ok = resp.status_code in (200, 202)
        if not ok:
            print(f"SendGrid no aceptó el envío: {resp.status_code} {getattr(resp, 'body', '')}")
        else:
            print(f"Correo de transferencia aceptado por SendGrid ({resp.status_code}) para {to_email}")
        return ok
    except Exception as e:
        print(f"Error al enviar email de transferencia: {e}")
        return False


def send_transfer_request_whatsapp(to_phone: str, solicitante_nombre: str, codigo: str, animales: List[Animal]) -> bool:
    whatsapp_token = os.getenv("WHATSAPP_TOKEN") or os.getenv("WHATSAPP_API_TOKEN")
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    if not whatsapp_token or not phone_number_id:
        print("Falta WHATSAPP_TOKEN/WHATSAPP_API_TOKEN o WHATSAPP_PHONE_NUMBER_ID")
        return False

    formatted_to_phone = to_phone[1:] if to_phone.startswith('+') else to_phone
    nombres_animales = ", ".join([animal.nombre for animal in animales]) if animales else "N/A"

    api_url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
    headers = {"Authorization": f"Bearer {whatsapp_token}", "Content-Type": "application/json"}

    payload = {
        "messaging_product": "whatsapp",
        "to": formatted_to_phone,
        "type": "template",
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
        r = requests.post(api_url, headers=headers, json=payload)
        r.raise_for_status()
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
) -> bool:
    api_key = os.getenv("SENDGRID_API_KEY")
    from_email = os.getenv("FROM_EMAIL")
    if not api_key or not from_email:
        print("Falta SENDGRID_API_KEY o FROM_EMAIL")
        return False

    message = Mail(
        from_email=from_email,
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
        sg = SendGridAPIClient(api_key)
        resp = sg.send(message)
        ok = resp.status_code in (200, 202)
        if not ok:
            print(f"SendGrid no aceptó el envío: {resp.status_code} {getattr(resp, 'body', '')}")
        else:
            print(f"Notificación de soporte aceptada por SendGrid ({resp.status_code}) para {admin_email}")
        return ok
    except Exception as e:
        print(f"Error al enviar email de soporte: {e}")
        return False
