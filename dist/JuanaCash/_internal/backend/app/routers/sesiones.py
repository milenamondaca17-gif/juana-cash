from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta
from ..database import get_db
from ..models.sesion_log import SesionLog
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/sesiones", tags=["Sesiones"])

class SesionCreate(BaseModel):
    usuario_id: int
    nombre_cajero: str
    turno: Optional[str] = None
    accion: str
    detalle: Optional[str] = None

@router.post("/registrar")
def registrar_sesion(datos: SesionCreate, db: Session = Depends(get_db)):
    sesion = SesionLog(
        usuario_id=datos.usuario_id,
        nombre_cajero=datos.nombre_cajero,
        turno=datos.turno,
        accion=datos.accion,
        detalle=datos.detalle
    )
    db.add(sesion)
    db.commit()
    return {"ok": True}

@router.get("/hoy")
def sesiones_hoy(db: Session = Depends(get_db)):
    hoy = date.today()
    sesiones = db.query(SesionLog).filter(
        func.date(SesionLog.fecha) == hoy
    ).order_by(SesionLog.fecha.desc()).all()
    return [
        {
            "id": s.id,
            "cajero": s.nombre_cajero,
            "turno": s.turno,
            "accion": s.accion,
            "detalle": s.detalle,
            "hora": s.fecha.strftime("%H:%M:%S")
        }
        for s in sesiones
    ]

@router.get("/historial")
def historial_sesiones(dias: int = 7, db: Session = Depends(get_db)):
    desde = date.today() - timedelta(days=dias)
    sesiones = db.query(SesionLog).filter(
        func.date(SesionLog.fecha) >= desde
    ).order_by(SesionLog.fecha.desc()).limit(200).all()
    return [
        {
            "id": s.id,
            "cajero": s.nombre_cajero,
            "turno": s.turno,
            "accion": s.accion,
            "detalle": s.detalle,
            "fecha": s.fecha.strftime("%d/%m/%Y %H:%M:%S")
        }
        for s in sesiones
    ]