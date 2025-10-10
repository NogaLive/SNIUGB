from sqlalchemy import (Column, String, DateTime, func, ForeignKey, Integer, 
                          Enum as SQLAlchemyEnum, Text, Boolean)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import uuid
import enum
import random

Base = declarative_base()

# --- CLASES ENUM DE PYTHON (Nombres Únicos y Descriptivos) ---

class UserRole(enum.Enum):
    GANADERO = "ganadero"
    ADMIN = "admin"

class AnimalCondicionSalud(enum.Enum):
    SANO = "Sano"
    EN_OBSERVACION = "En Observación"
    ENFERMO = "Enfermo"

class EventoSanitarioTipo(enum.Enum):
    VACUNACION = "Vacunación"
    TRATAMIENTO = "Tratamiento"
    DESPARASITACION = "Desparasitación"

class EventoProduccionTipo(enum.Enum):
    PESAJE = "Pesaje"
    PARTO = "Parto"
    CONTROL_LECHERO = "Control Lechero"

class TransferenciaEstado(enum.Enum):
    PENDIENTE = "Pendiente"
    APROBADA = "Aprobada"
    RECHAZADA = "Rechazada"
    EXPIRADA = "Expirada"
    
class CalendarioEventoTipo(enum.Enum):
    RECORDATORIO = "Recordatorio"
    EVENTO = "Evento"

class InventarioCategoria(enum.Enum):
    ALIMENTO = "Alimento"
    MEDICAMENTO = "Medicamento"
    VACUNA = "Vacuna"
    EQUIPO = "Equipo"


# --- MODELOS DE LAS TABLAS ---

class Raza(Base):
    __tablename__ = "razas"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, index=True, nullable=False)
    digito_especie = Column(String(1), nullable=False)

class Departamento(Base):
    __tablename__ = "departamentos"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, index=True, nullable=False)
    codigo_ubigeo = Column(String(2), nullable=False)

class Usuario(Base):
    __tablename__ = "datos_del_usuario"
    numero_de_dni = Column(String, primary_key=True, index=True)
    nombre_completo = Column(String, index=True, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    telefono = Column(String, nullable=False)
    password = Column(String, nullable=False)
    estado = Column(String, default="activo")
    rol = Column(SQLAlchemyEnum(UserRole, name='user_role_enum'), default=UserRole.GANADERO, nullable=False)
    fecha_de_registro = Column(DateTime(timezone=True), server_default=func.now())
    reset_token = Column(String, nullable=True)
    reset_token_expires = Column(DateTime(timezone=True), nullable=True)
    predios = relationship("Predio", back_populates="propietario")
    

def generate_predio_code():
    return f"PRD-{uuid.uuid4().hex[:6].upper()}"

class Predio(Base):
    __tablename__ = "predios"
    codigo_predio = Column(String, primary_key=True, default=generate_predio_code)
    nombre_predio = Column(String, nullable=False)
    departamento = Column(String, nullable=False)
    ubicacion = Column(String, nullable=False)
    propietario_dni = Column(String, ForeignKey("datos_del_usuario.numero_de_dni"), nullable=False)
    propietario = relationship("Usuario", back_populates="predios")
    animales = relationship("Animal", back_populates="predio")
    inventario_items = relationship("InventarioItem", back_populates="predio")

class Animal(Base):
    __tablename__ = "animales"
    cui = Column(String(11), primary_key=True, index=True)
    nombre = Column(String)
    raza_id = Column(Integer, ForeignKey("razas.id"))
    raza = relationship("Raza")
    sexo = Column(String)
    fecha_nacimiento = Column(DateTime(timezone=True))
    peso = Column(String)
    condicion_salud = Column(SQLAlchemyEnum(AnimalCondicionSalud, name='animal_condicion_salud_enum'), default=AnimalCondicionSalud.SANO)
    estado = Column(String, default="activo", index=True)
    predio_codigo = Column(String, ForeignKey("predios.codigo_predio"))
    predio = relationship("Predio", back_populates="animales")
    eventos_sanitarios = relationship("EventoSanitario", cascade="all, delete-orphan")
    eventos_produccion = relationship("EventoProduccion", cascade="all, delete-orphan")

class EventoSanitario(Base):
    __tablename__ = "eventos_sanitarios"
    id = Column(Integer, primary_key=True, index=True)
    animal_cui = Column(String(11), ForeignKey("animales.cui"), nullable=False)
    fecha_evento = Column(DateTime(timezone=True), nullable=False)
    tipo_evento = Column(SQLAlchemyEnum(EventoSanitarioTipo, name='evento_sanitario_tipo_enum'), nullable=False)
    producto_nombre = Column(String)
    dosis = Column(String)
    observaciones = Column(Text, nullable=True)

class EventoProduccion(Base):
    __tablename__ = "eventos_produccion"
    id = Column(Integer, primary_key=True, index=True)
    animal_cui = Column(String(11), ForeignKey("animales.cui"), nullable=False)
    fecha_evento = Column(DateTime(timezone=True), nullable=False)
    tipo_evento = Column(SQLAlchemyEnum(EventoProduccionTipo, name='evento_produccion_tipo_enum'), nullable=False)
    valor = Column(String)
    observaciones = Column(Text, nullable=True)

class TransferenciaAnimal(Base):
    __tablename__ = 'transferencia_animal_association'
    transferencia_id = Column(Integer, ForeignKey('transferencias.id'), primary_key=True)
    animal_cui = Column(String(11), ForeignKey('animales.cui'), primary_key=True)

class Transferencia(Base):
    __tablename__ = "transferencias"
    id = Column(Integer, primary_key=True, index=True)
    codigo_transferencia = Column(String, unique=True, index=True, default=lambda: f"TRANS-{uuid.uuid4().hex[:8].upper()}")
    codigo_confirmacion = Column(String, index=True, default=lambda: str(random.randint(100000, 999999)))
    solicitante_dni = Column(String, ForeignKey("datos_del_usuario.numero_de_dni"), nullable=False)
    receptor_dni = Column(String, ForeignKey("datos_del_usuario.numero_de_dni"), nullable=False)
    predio_destino_codigo = Column(String, ForeignKey("predios.codigo_predio"), nullable=False)
    estado = Column(SQLAlchemyEnum(TransferenciaEstado, name='transferencia_estado_enum'), default=TransferenciaEstado.PENDIENTE)
    fecha_solicitud = Column(DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = Column(DateTime(timezone=True), onupdate=func.now())
    animales = relationship("Animal", secondary="transferencia_animal_association")
    solicitante = relationship("Usuario", foreign_keys=[solicitante_dni])
    receptor = relationship("Usuario", foreign_keys=[receptor_dni])
    
class InventarioItem(Base):
    __tablename__ = "inventario_items"
    id = Column(Integer, primary_key=True, index=True)
    nombre_item = Column(String, nullable=False)
    categoria = Column(SQLAlchemyEnum(InventarioCategoria, name='inventario_categoria_enum'), nullable=False)
    descripcion = Column(Text, nullable=True)
    stock = Column(Integer, default=0)
    unidad_medida = Column(String)
    cantidad_alerta = Column(Integer, nullable=True)
    predio_codigo = Column(String, ForeignKey("predios.codigo_predio"), nullable=False)
    predio = relationship("Predio", back_populates="inventario_items")

class Notificacion(Base):
    __tablename__ = "notificaciones"
    id = Column(Integer, primary_key=True, index=True)
    usuario_dni = Column(String, ForeignKey("datos_del_usuario.numero_de_dni"), nullable=False)
    mensaje = Column(String, nullable=False)
    leida = Column(Boolean, default=False)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    link = Column(String, nullable=True)
    
class Evento(Base):
    __tablename__ = "eventos_calendario"
    id = Column(Integer, primary_key=True, index=True)
    usuario_dni = Column(String, ForeignKey("datos_del_usuario.numero_de_dni"), nullable=False)
    fecha_evento = Column(DateTime(timezone=True), nullable=False)
    titulo = Column(String, nullable=False)
    descripcion = Column(Text, nullable=True)
    tipo = Column(SQLAlchemyEnum(CalendarioEventoTipo, name='calendario_evento_tipo_enum'), nullable=False)
    es_completado = Column(Boolean, default=False)
    origen_tipo = Column(String, nullable=True)
    origen_id = Column(String, nullable=True)

class Categoria(Base):
    __tablename__ = "categorias"
    id = Column(Integer, primary_key=True)
    nombre = Column(String, unique=True, nullable=False)
    imagen_url = Column(String, nullable=False)
    
class Articulo(Base):
    __tablename__ = "articulos"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, nullable=False)
    resumen = Column(Text)
    contenido_html = Column(Text)
    imagen_principal = Column(String)
    categoria_id = Column(Integer, ForeignKey("categorias.id"))
    categoria = relationship("Categoria")
    estado_publicacion = Column(String, default="publicado")
    fecha_publicacion = Column(DateTime(timezone=True), server_default=func.now())
    autor_dni = Column(String, ForeignKey("datos_del_usuario.numero_de_dni"))

class TipoContenidoAyuda(enum.Enum):
    FAQ = "FAQ"
    VIDEO = "Video"

class ContenidoAyuda(Base):
    __tablename__ = "contenido_ayuda"
    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(SQLAlchemyEnum(TipoContenidoAyuda, name='tipo_contenido_ayuda_enum'), nullable=False)
    pregunta_titulo = Column(String, nullable=False)
    respuesta_contenido = Column(Text, nullable=True) # Para el texto de la FAQ
    video_url = Column(String, nullable=True) # Para el enlace del video tutorial
    orden = Column(Integer, default=0) # Para ordenar las preguntas

class SolicitudSoporte(Base):
    __tablename__ = "solicitudes_soporte"
    id = Column(Integer, primary_key=True, index=True)
    usuario_dni = Column(String, ForeignKey("datos_del_usuario.numero_de_dni"), nullable=False)
    categoria = Column(String, nullable=False)
    mensaje = Column(Text, nullable=False)
    estado = Column(String, default="Abierto")
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())