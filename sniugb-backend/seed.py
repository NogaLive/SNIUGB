from src.config.database import SessionLocal
from src.models.database_models import Base, Raza, Departamento

# Crea las tablas si no existen
# Obtiene una sesión de la base de datos
db = SessionLocal()

try:
    # --- Poblar Departamentos ---
    print("Poblando departamentos...")
    departamentos = [
        Departamento(nombre="AMAZONAS", codigo_ubigeo="01"), Departamento(nombre="ANCASH", codigo_ubigeo="02"),
        Departamento(nombre="APURIMAC", codigo_ubigeo="03"), Departamento(nombre="AREQUIPA", codigo_ubigeo="04"),
        Departamento(nombre="AYACUCHO", codigo_ubigeo="05"), Departamento(nombre="CAJAMARCA", codigo_ubigeo="06"),
        Departamento(nombre="CALLAO", codigo_ubigeo="07"), Departamento(nombre="CUSCO", codigo_ubigeo="08"),
        Departamento(nombre="HUANCAVELICA", codigo_ubigeo="09"), Departamento(nombre="HUANUCO", codigo_ubigeo="10"),
        Departamento(nombre="ICA", codigo_ubigeo="11"), Departamento(nombre="JUNIN", codigo_ubigeo="12"),
        Departamento(nombre="LA LIBERTAD", codigo_ubigeo="13"), Departamento(nombre="LAMBAYEQUE", codigo_ubigeo="14"),
        Departamento(nombre="LIMA", codigo_ubigeo="15"), Departamento(nombre="LORETO", codigo_ubigeo="16"),
        Departamento(nombre="MADRE DE DIOS", codigo_ubigeo="17"), Departamento(nombre="MOQUEGUA", codigo_ubigeo="18"),
        Departamento(nombre="PASCO", codigo_ubigeo="19"), Departamento(nombre="PIURA", codigo_ubigeo="20"),
        Departamento(nombre="PUNO", codigo_ubigeo="21"), Departamento(nombre="SAN MARTIN", codigo_ubigeo="22"),
        Departamento(nombre="TACNA", codigo_ubigeo="23"), Departamento(nombre="TUMBES", codigo_ubigeo="24"),
        Departamento(nombre="UCAYALI", codigo_ubigeo="25")
    ]
    for depto in departamentos:
        # Revisa si ya existe para no duplicar
        exists = db.query(Departamento).filter(Departamento.nombre == depto.nombre).first()
        if not exists:
            db.add(depto)

    # --- Poblar Razas ---
    print("Poblando razas...")
    razas = [
        Raza(nombre="HOLSTEIN", digito_especie="1"), Raza(nombre="BROWN SWISS", digito_especie="2"),
        Raza(nombre="ANGUS", digito_especie="3"), Raza(nombre="GYR", digito_especie="4"),
        Raza(nombre="GIROLANDO", digito_especie="5"), Raza(nombre="BRAHMAN", digito_especie="6"),
        Raza(nombre="CRIOLLO", digito_especie="7")
    ]
    for raza in razas:
        exists = db.query(Raza).filter(Raza.nombre == raza.nombre).first()
        if not exists:
            db.add(raza)

    db.commit()
    print("✅ Tablas maestras pobladas exitosamente.")

except Exception as e:
    db.rollback()
    print(f"❌ Error al poblar las tablas: {e}")

finally:
    db.close()