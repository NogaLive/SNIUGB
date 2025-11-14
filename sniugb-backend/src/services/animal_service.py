from sqlalchemy.orm import Session
from sqlalchemy import func, text
from src.models.database_models import Animal, Raza, Departamento

# --- Implementación del Algoritmo de Luhn ---
def calcular_digito_luhn(numero_sin_verificar: str) -> str:
    suma = 0
    num_digitos = len(numero_sin_verificar)
    paridad = num_digitos % 2

    for i, digito_str in enumerate(numero_sin_verificar):
        digito = int(digito_str)
        if i % 2 == paridad:
            digito *= 2
        if digito > 9:
            digito -= 9
        suma += digito
    
    return str((10 - (suma % 10)) % 10)

# --- Lógica de Generación del CUI ---
def generar_nuevo_cui(db: Session, departamento_nombre: str, raza_nombre: str) -> str:
    """
    Genera un nuevo Código Único de Identificación completo, con serialización por
    departamento Y raza.
    """
    # 1. Obtener dígito de especie/raza desde la BD
    raza_obj = db.query(Raza).filter(func.upper(Raza.nombre) == raza_nombre.upper()).first()
    if not raza_obj:
        raise ValueError("La raza especificada no es válida.")
    digito_especie = raza_obj.digito_especie

    # 2. Obtener código de departamento desde la BD
    depto_obj = db.query(Departamento).filter(func.upper(Departamento.nombre) == departamento_nombre.upper()).first()
    if not depto_obj:
        raise ValueError("El departamento especificado no es válido.")
    codigo_depto = depto_obj.codigo_ubigeo

        # 3. Obtener el siguiente número de serie
    # La consulta ahora filtra tanto por departamento como por dígito de especie.
    query = text(
        "SELECT MAX(CAST(SUBSTRING(cui FROM 4 FOR 7) AS INTEGER)) "
        "FROM animales "
        "WHERE SUBSTRING(cui FROM 2 FOR 2) = :codigo_depto "
        "AND SUBSTRING(cui FROM 1 FOR 1) = :digito_especie"
    )
    ultimo_serial = db.execute(
        query,
        {"codigo_depto": codigo_depto, "digito_especie": str(digito_especie)}
    ).scalar_one_or_none()

    nuevo_serial = (ultimo_serial or 0) + 1
    serial_str = str(nuevo_serial).zfill(7)

    # 4. Construir el CUI base de 10 dígitos
    cui_base = f"{digito_especie}{codigo_depto}{serial_str}"

    # 5. Calcular el dígito de control de Luhn
    digito_control = calcular_digito_luhn(cui_base)

    # 6. Unir todo para el CUI final de 11 dígitos
    cui_final = f"{cui_base}{digito_control}"

    return cui_final