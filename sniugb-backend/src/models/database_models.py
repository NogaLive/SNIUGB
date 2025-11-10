from sqlalchemy import (
    Column, String, DateTime, func, ForeignKey, Integer, text,
    Enum as SQLAlchemyEnum, Text, Boolean, Float
)
from sqlalchemy.orm import relationship
from sqlalchemy.orm import declarative_base
import uuid
import enum
import random

Base = declarative_base()

# -------- ENUMS FIJOS (solo los que acordamos mantener fijos) --------

class UserRole(enum.Enum):
    GANADERO = "ganadero"
    ADMIN = "admin"

class AnimalCondicionSalud(enum.Enum):
    SANO = "Sano"
    EN_OBSERVACION = "En Observación"
    ENFERMO = "Enfermo"

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

# Producción fija: LECHE/CARNE/CUERO + PESAJE (reutilizamos la misma tabla)
class ProduccionTipo(enum.Enum):
    LECHE = "LECHE"
    CARNE = "CARNE"
    CUERO = "CUERO"
    PESAJE = "PESAJE"

# --------- NUEVO: Tipos de evento dinámicos ---------
# Se gestionan por ADMIN; se usan por Sanidad y Control de Calidad
# grupos esperados: "ENFERMEDAD" | "TRATAMIENTO" | "CONTROL_CALIDAD"
class TipoEvento(Base):
    __tablename__ = "tipo_evento"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False, unique=True)
    grupo = Column(String, nullable=False)
    multi_animal = Column(Boolean, nullable=False, server_default=text("false"))

# --------- Catálogos previos ---------

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

# --------- Usuario / Predio ---------

class Usuario(Base):
    __tablename__ = "datos_del_usuario"
    numero_de_dni = Column(String, primary_key=True, index=True)
    nombre_completo = Column(String, index=True, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    telefono = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    estado = Column(String, default="activo")
    rol = Column(SQLAlchemyEnum(UserRole, name='user_role_enum'), default=UserRole.GANADERO, nullable=False)
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
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

# --------- Animal ---------

class Animal(Base):
    __tablename__ = "animales"
    cui = Column(String(11), primary_key=True, index=True)
    nombre = Column(String)
    raza_id = Column(Integer, ForeignKey("razas.id"))
    raza = relationship("Raza")
    sexo = Column(String)  # "MACHO"/"HEMBRA"
    fecha_nacimiento = Column(DateTime(timezone=True))
    peso = Column(String)  # legado, mantenemos
    condicion_salud = Column(SQLAlchemyEnum(AnimalCondicionSalud, name='animal_condicion_salud_enum'), default=AnimalCondicionSalud.SANO)
    estado = Column(String, default="activo", index=True)
    predio_codigo = Column(String, ForeignKey("predios.codigo_predio"))
    predio = relationship("Predio", back_populates="animales")

    # NUEVO: relaciones parentales para genealogía (simple)
    padre_cui = Column(String(11), ForeignKey("animales.cui"), nullable=True)
    madre_cui = Column(String(11), ForeignKey("animales.cui"), nullable=True)

    eventos_sanitarios = relationship("EventoSanitarioAnimal", cascade="all, delete-orphan")
    eventos_produccion = relationship("EventoProduccion", cascade="all, delete-orphan")

# --------- Sanidad (evento principal + asociación a animales) ---------

class EventoSanitario(Base):
    __tablename__ = "eventos_sanitarios"
    id = Column(Integer, primary_key=True, index=True)

    # Enfermedad (obligatorio)
    fecha_evento_enfermedad = Column(DateTime(timezone=True), nullable=False)
    tipo_evento_enfermedad_id = Column(Integer, ForeignKey("tipo_evento.id"), nullable=False)
    tipo_enfermedad = relationship("TipoEvento", foreign_keys=[tipo_evento_enfermedad_id])

    # Tratamiento (opcional)
    fecha_evento_tratamiento = Column(DateTime(timezone=True), nullable=True)
    tipo_evento_tratamiento_id = Column(Integer, ForeignKey("tipo_evento.id"), nullable=True)
    tipo_tratamiento = relationship("TipoEvento", foreign_keys=[tipo_evento_tratamiento_id])
    nombre_tratamiento = Column(String, nullable=True)
    dosis = Column(Float, nullable=True)            # cantidad numérica
    unidad_medida_dosis = Column(String, nullable=True)  # ml, mg, etc.

    observaciones = Column(Text, nullable=True)

    creador_dni = Column(String, ForeignKey("datos_del_usuario.numero_de_dni"), nullable=False)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())

class EventoSanitarioAnimal(Base):
    __tablename__ = "evento_sanitario_animales"
    evento_id = Column(Integer, ForeignKey("eventos_sanitarios.id"), primary_key=True)
    animal_cui = Column(String(11), ForeignKey("animales.cui"), primary_key=True)

# --------- Producción (incluye PESAJE como tipo) ---------

class EventoProduccion(Base):
    __tablename__ = "eventos_produccion"
    id = Column(Integer, primary_key=True, index=True)
    animal_cui = Column(String(11), ForeignKey("animales.cui"), nullable=False, index=True)
    fecha_evento = Column(DateTime(timezone=True), nullable=False)
    tipo_evento = Column(SQLAlchemyEnum(ProduccionTipo, name='produccion_tipo_enum'), nullable=False)

    # valores normalizados
    valor_cantidad = Column(Float, nullable=True)   # ej 12.0
    unidad_medida = Column(String, nullable=True)   # L, kg, g, ml, etc.
    observaciones = Column(Text, nullable=True)

# --------- Control de Calidad (masivo) ---------

class ControlCalidad(Base):
    __tablename__ = "control_calidad"
    id = Column(Integer, primary_key=True, index=True)
    fecha_evento = Column(DateTime(timezone=True), nullable=False)

    tipo_evento_calidad_id = Column(Integer, ForeignKey("tipo_evento.id"), nullable=False)  # grupo CONTROL_CALIDAD
    tipo_calidad = relationship("TipoEvento", foreign_keys=[tipo_evento_calidad_id])

    producto = Column(SQLAlchemyEnum(ProduccionTipo, name='control_producto_enum'), nullable=False)  # LECHE/CARNE/CUERO
    valor_cantidad = Column(Float, nullable=True)
    unidad_medida = Column(String, nullable=True)
    observaciones = Column(Text, nullable=True)

    creador_dni = Column(String, ForeignKey("datos_del_usuario.numero_de_dni"), nullable=False)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())

class ControlCalidadAnimal(Base):
    __tablename__ = "control_calidad_animales"
    control_id = Column(Integer, ForeignKey("control_calidad.id"), primary_key=True)
    animal_cui = Column(String(11), ForeignKey("animales.cui"), primary_key=True)

# --------- Transferencias, Inventario, Notificaciones, Calendario, Blog ---------

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
    categoria_id = Column(Integer, nullable=True, name="categoria_id")  # <-- usar la columna real
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
    slug = Column(String, unique=True, index=True, nullable=False)
    resumen = Column(Text)
    contenido_html = Column(Text)
    imagen_thumbnail_url = Column(String, nullable=True)
    imagen_display_url = Column(String, nullable=True)
    vistas = Column(Integer, default=0)
    categoria_id = Column(Integer, ForeignKey("categorias.id"))
    categoria = relationship("Categoria")
    estado_publicacion = Column(String, default="publicado")
    fecha_publicacion = Column(DateTime(timezone=True), server_default=func.now())
    autor_dni = Column(String, ForeignKey("datos_del_usuario.numero_de_dni"))
    autor = relationship("Usuario")

class TipoContenidoAyuda(enum.Enum):
    FAQ = "FAQ"
    VIDEO = "Video"

class ContenidoAyuda(Base):
    __tablename__ = "contenido_ayuda"
    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(SQLAlchemyEnum(TipoContenidoAyuda, name='tipo_contenido_ayuda_enum'), nullable=False)
    pregunta_titulo = Column(String, nullable=False)
    respuesta_contenido = Column(Text, nullable=True)
    video_url = Column(String, nullable=True)
    orden = Column(Integer, default=0)

class SolicitudSoporte(Base):
    __tablename__ = "solicitudes_soporte"
    id = Column(Integer, primary_key=True, index=True)
    usuario_dni = Column(String, ForeignKey("datos_del_usuario.numero_de_dni"), nullable=False)
    categoria = Column(String, nullable=False)
    mensaje = Column(Text, nullable=False)
    estado = Column(String, default="Abierto")
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id = Column(Integer, primary_key=True, index=True)
    jti = Column(String, unique=True, index=True, nullable=False)
    usuario_dni = Column(String, ForeignKey("datos_del_usuario.numero_de_dni"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("Usuario", back_populates="refresh_tokens")