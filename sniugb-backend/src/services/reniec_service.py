import requests
import os
from dotenv import load_dotenv

load_dotenv()

APIPERU_TOKEN = os.getenv("APIPERU_TOKEN")
# CORRECCIÓN: La URL base no debe tener el DNI.
API_URL = "https://apiperu.dev/api/dni" 

def get_data_from_reniec(dni: str) -> dict | None:
    """
    Consulta la API externa para obtener datos de RENIEC a partir de un DNI,
    usando el método GET y manejando los errores de forma robusta.
    """
    if not APIPERU_TOKEN:
        print("ERROR: No se encontró el token de ApiPeru en el archivo .env")
        return None

    # CORRECCIÓN: Se construye la URL completa, añadiendo el DNI al final.
    full_url = f"{API_URL}/{dni}"
    
    headers = {
        'Authorization': f'Bearer {APIPERU_TOKEN}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    try:
        # CORRECCIÓN: Se usa requests.get() en lugar de requests.post()
        # y se elimina el parámetro 'json'.
        response = requests.get(full_url, headers=headers)

        # Esta línea lanzará una excepción para errores como 404, 500, etc.
        response.raise_for_status() 
        
        data = response.json()
        if data.get("success"):
            # Se extrae el nombre y se limpian espacios extra.
            nombre = data["data"].get("nombres", "")
            apellido_paterno = data["data"].get("apellido_paterno", "")
            apellido_materno = data["data"].get("apellido_materno", "")
            
            return {
                "nombre_completo": f"{nombre} {apellido_paterno} {apellido_materno}".strip()
            }
        else:
            print(f"ApiPeru devolvió un error de negocio: {data.get('message', 'Error desconocido')}")
            return None

    except requests.exceptions.HTTPError as e:
        # Este bloque se activa si raise_for_status() detecta un error.
        # Es ideal para manejar el error 404 (DNI no encontrado).
        if e.response.status_code == 404:
            print(f"DNI no encontrado en ApiPeru: {dni}")
        else:
            print(f"Error HTTP inesperado desde ApiPeru: {e.response.status_code} - {e.response.text}")
        return None
            
    except requests.exceptions.RequestException as e:
        # Para cualquier otro tipo de error (ej. problemas de red, timeout).
        print(f"Error de conexión al consultar la API de RENIEC: {e}")
        return None