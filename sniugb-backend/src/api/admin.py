from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import inspect
from datetime import datetime
from typing import List
from PIL import Image
import pandas as pd
import zipfile
import shutil
import uuid
import io
import os
import aiofiles
from slugify import slugify

# Imports de la aplicación
from src.utils.security import get_current_admin_user, get_db, get_current_user
from src.models.database_models import (
    Usuario, Base, Raza, Departamento, Articulo, Categoria, ContenidoAyuda
)
from src.models.user_models import UserResponseSchema
from src.models.soporte_models import ContenidoAyudaResponseSchema
from src.models.admin_models import (
    RazaCreateUpdateSchema, RazaResponseSchema, 
    DepartamentoCreateUpdateSchema, DepartamentoResponseSchema,
    ArticuloSchema, CategoriaCreateUpdateSchema, CategoriaSchema
)

# Router principal para la sección de administración
admin_router = APIRouter(
    prefix="/admin", 
    tags=["Panel de Administración"],
    dependencies=[Depends(get_current_admin_user)],
    route_class=APIRoute
)

# --- Gestión de Usuarios ---
@admin_router.get("/users", response_model=List[UserResponseSchema])
async def get_all_users(db: Session = Depends(get_db)):
    """(Admin) Obtiene una lista de todos los usuarios registrados."""
    return db.query(Usuario).order_by(Usuario.fecha_de_registro.desc()).all()

@admin_router.put("/users/{dni}/toggle-status", response_model=UserResponseSchema)
async def toggle_user_status(dni: str, db: Session = Depends(get_db)):
    """(Admin) Activa o desactiva la cuenta de un usuario."""
    user = db.query(Usuario).filter(Usuario.numero_de_dni == dni).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    
    user.estado = "inactivo" if user.estado == "activo" else "activo"
    db.commit()
    db.refresh(user)
    return user

# --- Gestión de Tablas Maestras (Razas y Departamentos) ---
# (Estos endpoints se mantienen como estaban, ya que son correctos)
@admin_router.get("/razas", response_model=List[RazaResponseSchema])
async def get_razas_admin(db: Session = Depends(get_db)):
    return db.query(Raza).all()

@admin_router.post("/razas", response_model=RazaResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_raza(raza_data: RazaCreateUpdateSchema, db: Session = Depends(get_db)):
    nueva_raza = Raza(**raza_data.model_dump())
    db.add(nueva_raza)
    db.commit()
    db.refresh(nueva_raza)
    return nueva_raza

@admin_router.put("/razas/{raza_id}", response_model=RazaResponseSchema)
async def update_raza(raza_id: int, raza_data: RazaCreateUpdateSchema, db: Session = Depends(get_db)):
    """(Admin) Actualiza una raza existente."""
    raza = db.query(Raza).filter(Raza.id == raza_id).first()
    if not raza:
        raise HTTPException(status_code=404, detail="Raza no encontrada.")
    
    raza.nombre = raza_data.nombre
    raza.digito_especie = raza_data.digito_especie
    db.commit()
    db.refresh(raza)
    return raza

@admin_router.delete("/razas/{raza_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_raza(raza_id: int, db: Session = Depends(get_db)):
    """(Admin) Elimina una raza."""
    raza = db.query(Raza).filter(Raza.id == raza_id).first()
    if not raza:
        raise HTTPException(status_code=404, detail="Raza no encontrada.")
    db.delete(raza)
    db.commit()
    return None

# --- DEPARTAMENTOS ---
@admin_router.get("/departamentos", response_model=List[DepartamentoResponseSchema])
async def get_departamentos_admin(db: Session = Depends(get_db)):
    """(Admin) Obtiene la lista de todos los departamentos."""
    return db.query(Departamento).all()

@admin_router.post("/departamentos", response_model=DepartamentoResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_departamento(depto_data: DepartamentoCreateUpdateSchema, db: Session = Depends(get_db)):
    """(Admin) Crea un nuevo departamento."""
    nuevo_depto = Departamento(**depto_data.model_dump())
    db.add(nuevo_depto)
    db.commit()
    db.refresh(nuevo_depto)
    return nuevo_depto

@admin_router.put("/departamentos/{depto_id}", response_model=DepartamentoResponseSchema)
async def update_departamento(depto_id: int, depto_data: DepartamentoCreateUpdateSchema, db: Session = Depends(get_db)):
    """(Admin) Actualiza un departamento existente."""
    depto = db.query(Departamento).filter(Departamento.id == depto_id).first()
    if not depto:
        raise HTTPException(status_code=404, detail="Departamento no encontrado.")
    
    depto.nombre = depto_data.nombre
    depto.codigo_ubigeo = depto_data.codigo_ubigeo
    db.commit()
    db.refresh(depto)
    return depto

@admin_router.delete("/departamentos/{depto_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_departamento(depto_id: int, db: Session = Depends(get_db)):
    """(Admin) Elimina un departamento."""
    depto = db.query(Departamento).filter(Departamento.id == depto_id).first()
    if not depto:
        raise HTTPException(status_code=404, detail="Departamento no encontrado.")
    db.delete(depto)
    db.commit()
    return None

# --- Gestión de Contenido (Publicaciones) ---

@admin_router.get("/categorias", response_model=List[CategoriaSchema])
async def get_categorias_admin(db: Session = Depends(get_db)):
    """(Admin) Obtiene la lista de todas las categorías."""
    return db.query(Categoria).all()

@admin_router.post("/categorias", response_model=CategoriaSchema, status_code=201)
async def create_categoria(
    db: Session = Depends(get_db),
    nombre: str = Form(...),
    file: UploadFile = File(...)
):
    """(Admin) Crea una nueva categoría, sube una imagen y la redimensiona."""
    file_extension = file.filename.split(".")[-1].lower()
    if file_extension not in ["jpg", "jpeg", "png"]:
        raise HTTPException(status_code=400, detail="Formato de imagen no válido. Usar JPG o PNG.")
    
    file_name = f"{uuid.uuid4()}.{file_extension}"
    
    original_path = f"static/images/categorias/originals/{file_name}"
    thumbnail_path = f"static/images/categorias/thumbnails/{file_name}"
    
    os.makedirs("static/images/categorias/originals", exist_ok=True)
    os.makedirs("static/images/categorias/thumbnails", exist_ok=True)

    try:
        async with aiofiles.open(original_path, 'wb') as buffer:
            content = await file.read()
            await buffer.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar la imagen: {e}")

    try:
        with Image.open(original_path) as img:
            img.thumbnail((800, 600)) 
            img.save(thumbnail_path, optimize=True, quality=85)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar la imagen: {e}")

    # Se guarda solo el nombre del archivo en la BD
    nueva_categoria = Categoria(nombre=nombre, imagen_url=file_name)
    db.add(nueva_categoria)
    db.commit()
    db.refresh(nueva_categoria)
    
    return nueva_categoria

@admin_router.get("/publicaciones", response_model=List[ArticuloSchema])
async def get_all_articulos(db: Session = Depends(get_db)):
    """(Admin) Obtiene todos los artículos, cargando relaciones eficientemente."""
    articulos = db.query(Articulo).options(
        joinedload(Articulo.categoria),
        joinedload(Articulo.autor)
    ).order_by(Articulo.fecha_publicacion.desc()).all()
    return articulos

@admin_router.post("/publicaciones", response_model=ArticuloSchema, status_code=status.HTTP_201_CREATED)
async def create_articulo(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user), 
    titulo: str = Form(...),
    resumen: str = Form(...),
    contenido_html: str = Form(...),
    categoria_id: int = Form(...),
    imagen_principal: UploadFile = File(...)
):
    """(Admin) Crea una nueva publicación con subida y procesamiento de imagen en 3 versiones."""
    
    # 1. Validación y generación de nombre de archivo
    extension = imagen_principal.filename.split(".")[-1].lower()
    if extension not in ["jpg", "jpeg", "png"]:
        raise HTTPException(status_code=400, detail="Formato de imagen no válido.")
    
    file_name = f"{uuid.uuid4()}.{extension}"

    # 2. Definición de rutas y creación de directorios
    original_path = f"static/images/articulos/originals/{file_name}"
    display_path = f"static/images/articulos/display/{file_name}"
    thumbnail_path = f"static/images/articulos/thumbnails/{file_name}"

    os.makedirs("static/images/articulos/originals", exist_ok=True)
    os.makedirs("static/images/articulos/display", exist_ok=True)
    os.makedirs("static/images/articulos/thumbnails", exist_ok=True)

    # 3. Guardado del archivo original
    try:
        async with aiofiles.open(original_path, 'wb') as out_file:
            content = await imagen_principal.read()
            await out_file.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar imagen original: {e}")

    # 4. Procesamiento de imágenes (display y thumbnail)
    try:
        with Image.open(original_path) as img:
            # Versión de visualización (grande, para fondos)
            img_display = img.copy()
            img_display.thumbnail((1920, 1080))
            img_display.save(display_path, optimize=True, quality=85)

            # Versión de miniatura (pequeña, para listas)
            img_thumbnail = img.copy()
            img_thumbnail.thumbnail((400, 400))
            img_thumbnail.save(thumbnail_path, optimize=True, quality=80)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar las imágenes: {e}")

    # 5. Creación del registro en la base de datos
    nuevo_articulo = Articulo(
        titulo=titulo,
        slug=slugify(titulo),
        resumen=resumen,
        contenido_html=contenido_html,
        categoria_id=categoria_id,
        imagen_display_url=file_name,
        imagen_thumbnail_url=file_name,
        autor_dni=current_user.numero_de_dni,
        vistas=0
    )
    db.add(nuevo_articulo)
    db.commit()
    db.refresh(nuevo_articulo)
    return nuevo_articulo

@admin_router.put("/publicaciones/{articulo_id}", response_model=ArticuloSchema)
async def update_articulo(
    articulo_id: int, 
    articulo_data: ArticuloSchema,
    db: Session = Depends(get_db)
):
    """(Admin) Actualiza una publicación existente."""
    articulo = db.query(Articulo).filter(Articulo.id == articulo_id).first()
    if not articulo:
        raise HTTPException(status_code=404, detail="Artículo no encontrado.")
    
    update_data = articulo_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(articulo, key, value)
        
    db.commit()
    db.refresh(articulo)
    return articulo

@admin_router.delete("/publicaciones/{articulo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_articulo(articulo_id: int, db: Session = Depends(get_db)):
    """(Admin) Elimina una publicación."""
    articulo = db.query(Articulo).filter(Articulo.id == articulo_id).first()
    if not articulo:
        raise HTTPException(status_code=404, detail="Artículo no encontrado.")
    
    db.delete(articulo)
    db.commit()
    return None

# --- Backup de Base de Datos ---
@admin_router.get("/backup/db")
async def backup_database(db: Session = Depends(get_db)):
    """(Admin) Genera y descarga un .zip con todas las tablas en formato .csv."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        inspector = inspect(db.get_bind())
        table_names = inspector.get_table_names()

        for table_name in table_names:
            if table_name == 'alembic_version':
                continue
            
            df = pd.read_sql_table(table_name, db.get_bind())
            csv_string = df.to_csv(index=False, encoding='utf-8')
            zip_file.writestr(f"{table_name}.csv", csv_string)
            
    zip_buffer.seek(0)
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=sniugb_backup_{datetime.now().strftime('%Y%m%d')}.zip"}
    )

@admin_router.get("/ayuda", response_model=List[ContenidoAyudaResponseSchema])
async def get_ayuda_admin(db: Session = Depends(get_db)):
    """(Admin) Obtiene todo el contenido de la sección de ayuda."""
    return db.query(ContenidoAyuda).order_by(ContenidoAyuda.orden).all()

@admin_router.post("/ayuda", response_model=ContenidoAyudaResponseSchema, status_code=201)
async def create_ayuda_item(ayuda_data: ContenidoAyudaResponseSchema, db: Session = Depends(get_db)):
    """(Admin) Crea un nuevo item de ayuda (FAQ o Video)."""
    nuevo_item = ContenidoAyuda(**ayuda_data.model_dump())
    db.add(nuevo_item)
    db.commit()
    db.refresh(nuevo_item)
    return nuevo_item