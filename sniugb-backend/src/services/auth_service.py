from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

# Se importan los modelos de la base de datos y los esquemas de Pydantic
from src.models.user_models import UserCreateSchema
from src.models.database_models import Usuario

# Se importan las funciones de utilidad
from src.utils.security import get_password_hash
from .reniec_service import get_data_from_reniec

def create_new_user(user_data: UserCreateSchema, db: Session):
    """
    Crea un nuevo usuario, validando DNI, normalizando teléfono y obteniendo el nombre.
    """
    # 1. Validar DNI y obtener nombre desde el servicio externo
    reniec_data = get_data_from_reniec(user_data.numero_de_dni)
    if not reniec_data or not reniec_data.get("nombre_completo"):
        return "dni_not_found"

    # 2. Encriptar la contraseña
    hashed_password = get_password_hash(user_data.password)
    
    # 3. Normalizar el número de teléfono al formato E.164 (opcional pero recomendado)
    formatted_phone = user_data.telefono
    if not formatted_phone.startswith('+'):
        # Asume el código de país de Perú (+51)
        formatted_phone = f"+51{user_data.telefono}"

    # 4. Crear el objeto de usuario para la base de datos
    db_user = Usuario(
        # --- CORRECCIÓN AQUÍ ---
        # Se usa el nombre de campo correcto del schema: 'numero_de_dni' en lugar de 'dni'.
        numero_de_dni=user_data.numero_de_dni,
        nombre_completo=reniec_data["nombre_completo"],
        email=user_data.email,
        telefono=formatted_phone, # Se guarda el número ya formateado
        password=hashed_password
    )
    
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError as e:
        db.rollback()
        # Analizamos el mensaje de error de la base de datos
        error_info = str(e.orig).lower()
    
        # Si el error menciona la restricción del teléfono, devolvemos un código específico
        if 'telefono' in error_info:
            return "duplicate_phone"
        
        # Si no, asumimos que es el DNI o el email
        if 'email' in error_info or 'datos_del_usuario_pkey' in error_info:
            return "duplicate_entry"
        
        # Para cualquier otro error de integridad inesperado
        return "unexpected_db_error"