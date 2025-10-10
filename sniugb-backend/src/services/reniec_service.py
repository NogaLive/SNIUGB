import requests
import os
from dotenv import load_dotenv

load_dotenv()

APIPERU_TOKEN = os.getenv("APIPERU_TOKEN")
API_URL = "https://apiperu.dev/api/dni" 

def get_data_from_reniec(dni: str):
    if not APIPERU_TOKEN:
        print("ERROR: No se encontró el token de ApiPeru en el archivo .env")
        return None

    try:
        response = requests.post(
            API_URL,
            headers={
                'Authorization': f'Bearer {APIPERU_TOKEN}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            json={ "dni": dni }
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                return {
                    "nombre_completo": data["data"].get("nombre_completo", "").strip()
                }
            else:
                print(f"ApiPeru devolvió un error: {data.get('message', 'Error desconocido')}")
                return None
        else:
            print(f"Error HTTP desde ApiPeru: {response.status_code} - {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error de conexión al consultar la API de RENIEC: {e}")
        return None