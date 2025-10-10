from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from src.models.user_models import UserCreateSchema
from src.models.database_models import Usuario
from src.utils.security import get_password_hash
from .reniec_service import get_data_from_reniec

def create_new_user(user_data: UserCreateSchema, db: Session):
    """
    Crea un nuevo usuario, validando DNI, normalizando teléfono y obteniendo el nombre.
    """
    # 1. Validar DNI y obtener nombre desde el servicio externo
    reniec_data = get_data_from_reniec(user_data.dni)
    if not reniec_data or not reniec_data.get("nombre_completo"):
        return "dni_not_found" 

    # 2. Encriptar la contraseña
    hashed_password = get_password_hash(user_data.password)
    
    # 3. Normalizar el número de teléfono al formato E.164
    formatted_phone = user_data.telefono
    if not formatted_phone.startswith('+'):
        # Asume el código de país de Perú (+51)
        formatted_phone = f"+51{user_data.telefono}"

    # 4. Crear el objeto de usuario para la base de datos
    db_user = Usuario(
        numero_de_dni=user_data.dni,
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
    except IntegrityError:
        db.rollback()
        # Devuelve un código de error específico para email o DNI duplicado
        return "duplicate_entry"