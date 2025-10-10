from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import inspect
from typing import List
import pandas as pd
import io
import zipfile
from datetime import datetime

from src.utils.security import get_current_admin_user, get_db
from src.models.database_models import (
    Usuario, Base, Raza, Departamento, Articulo
)
from src.models.user_models import UserResponseSchema
from src.models.database_models import ContenidoAyuda, Categoria
from src.models.soporte_models import ContenidoAyudaResponseSchema
from src.models.admin_models import (
    RazaCreateUpdateSchema, RazaResponseSchema, 
    DepartamentoCreateUpdateSchema, DepartamentoResponseSchema,
    ArticuloSchema, ArticuloCreateSchema, ArticuloUpdateSchema, CategoriaSchema, CategoriaCreateUpdateSchema
)

# Protegemos todo el router con una dependencia.
# Cualquier endpoint aquí dentro requerirá que el usuario tenga el rol 'ADMIN'.
admin_router = APIRouter(
    prefix="/admin", 
    tags=["Panel de Administración"],
    dependencies=[Depends(get_current_admin_user)]
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

# --- Gestión de Tablas Maestras ---

# --- RAZAS ---
@admin_router.get("/razas", response_model=List[RazaResponseSchema])
async def get_razas_admin(db: Session = Depends(get_db)):
    """(Admin) Obtiene la lista de todas las razas."""
    return db.query(Raza).all()

@admin_router.post("/razas", response_model=RazaResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_raza(raza_data: RazaCreateUpdateSchema, db: Session = Depends(get_db)):
    """(Admin) Crea una nueva raza."""
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
async def create_categoria(categoria_data: CategoriaCreateUpdateSchema, db: Session = Depends(get_db)):
    """(Admin) Crea una nueva categoría."""
    nueva_categoria = Categoria(**categoria_data.model_dump())
    db.add(nueva_categoria)
    db.commit()
    db.refresh(nueva_categoria)
    return nueva_categoria

@admin_router.get("/publicaciones", response_model=List[ArticuloSchema])
async def get_all_articulos(db: Session = Depends(get_db)):
    """(Admin) Obtiene todos los artículos publicados."""
    return db.query(Articulo).order_by(Articulo.fecha_publicacion.desc()).all()

@admin_router.post("/publicaciones", response_model=ArticuloSchema, status_code=status.HTTP_201_CREATED)
async def create_articulo(
    articulo_data: ArticuloCreateSchema, 
    db: Session = Depends(get_db),
    admin_user: Usuario = Depends(get_current_admin_user)
):
    """(Admin) Crea una nueva publicación."""
    nuevo_articulo = Articulo(
        **articulo_data.model_dump(),
        autor_dni=admin_user.numero_de_dni
    )
    db.add(nuevo_articulo)
    db.commit()
    db.refresh(nuevo_articulo)
    return nuevo_articulo

@admin_router.put("/publicaciones/{articulo_id}", response_model=ArticuloSchema)
async def update_articulo(
    articulo_id: int, 
    articulo_data: ArticuloUpdateSchema, 
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