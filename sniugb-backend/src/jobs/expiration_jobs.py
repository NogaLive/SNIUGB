from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from src.models.database_models import Transferencia, TransferenciaEstado
from src.config.database import SessionLocal

def expire_old_transfer_requests():
    """
    Busca todas las solicitudes de transferencia pendientes que tengan más de 24 horas
    y actualiza su estado a 'Expirada'.
    """
    print(f"[{datetime.now()}] Ejecutando tarea de expiración de transferencias...")
    db: Session = SessionLocal()
    try:
        # 1. Calcular el punto de corte (hace 24 horas)
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)

        # 2. Buscar las solicitudes pendientes y antiguas
        solicitudes_a_expirar = db.query(Transferencia).filter(
            Transferencia.estado == TransferenciaEstado.PENDIENTE,
            Transferencia.fecha_solicitud < cutoff_time
        ).all()

        if not solicitudes_a_expirar:
            print("No se encontraron transferencias para expirar.")
            return

        # 3. Actualizar el estado de cada una
        for solicitud in solicitudes_a_expirar:
            solicitud.estado = TransferenciaEstado.EXPIRADA
        
        db.commit()
        print(f"✅ Se han expirado {len(solicitudes_a_expirar)} solicitudes.")

    except Exception as e:
        print(f"❌ Error durante la tarea de expiración: {e}")
        db.rollback()
    finally:
        db.close()