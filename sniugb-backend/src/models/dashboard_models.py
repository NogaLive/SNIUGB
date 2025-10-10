from pydantic import BaseModel

class KPISchema(BaseModel):
    total_hato: int
    alertas_salud: int
    tareas_para_hoy: int
    produccion_reciente_carne: float
    produccion_reciente_leche: float
    solicitudes_transferencia: int