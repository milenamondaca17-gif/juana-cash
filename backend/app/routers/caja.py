from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from datetime import datetime, date
from ..database import get_db
from ..models.caja_turno import CajaTurno
from ..models.venta import Venta

router = APIRouter(prefix="/caja", tags=["Caja"])

class AbrirCajaSchema(BaseModel):
    usuario_id: int
    monto_apertura: float = 0

class CerrarCajaSchema(BaseModel):
    monto_cierre: float = 0

@router.post("/abrir")
def abrir_caja(datos: AbrirCajaSchema, db: Session = Depends(get_db)):
    turno_abierto = db.query(CajaTurno).filter(
        CajaTurno.usuario_id == datos.usuario_id,
        CajaTurno.estado == "abierto"
    ).first()
    if turno_abierto:
        return {"id": turno_abierto.id, "mensaje": "Ya hay una caja abierta"}
    turno = CajaTurno(usuario_id=datos.usuario_id, monto_apertura=datos.monto_apertura, estado="abierto")
    db.add(turno)
    db.commit()
    db.refresh(turno)
    return {"id": turno.id, "mensaje": "Caja abierta", "monto_apertura": datos.monto_apertura}

@router.post("/cerrar/{turno_id}")
def cerrar_caja(turno_id: int, datos: CerrarCajaSchema, db: Session = Depends(get_db)):
    turno = db.query(CajaTurno).filter(CajaTurno.id == turno_id).first()
    if not turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    ventas_hoy = db.query(Venta).filter(
        func.date(Venta.fecha) == date.today(),
        Venta.estado == "completada"
    ).all()
    total_calculado = sum(float(v.total) for v in ventas_hoy)
    diferencia = datos.monto_cierre - total_calculado
    turno.cierre = datetime.now()
    turno.monto_cierre_declarado = datos.monto_cierre
    turno.monto_cierre_calculado = total_calculado
    turno.diferencia = diferencia
    turno.estado = "cerrado"
    db.commit()
    return {"mensaje": "Caja cerrada", "total_calculado": total_calculado, "diferencia": diferencia}

@router.get("/turno-actual/{usuario_id}")
def turno_actual(usuario_id: int, db: Session = Depends(get_db)):
    turno = db.query(CajaTurno).filter(
        CajaTurno.usuario_id == usuario_id,
        CajaTurno.estado == "abierto"
    ).first()
    if not turno:
        return {"abierto": False}
    return {"abierto": True, "id": turno.id, "monto_apertura": float(turno.monto_apertura)}

@router.get("/historial")
def historial_cierres(limite: int = 30, db: Session = Depends(get_db)):
    turnos = db.query(CajaTurno).filter(
        CajaTurno.estado == "cerrado"
    ).order_by(CajaTurno.cierre.desc()).limit(limite).all()
    return [{
        "id":                    t.id,
        "apertura":              str(t.apertura)[:16] if t.apertura else "",
        "cierre":                str(t.cierre)[:16] if t.cierre else "",
        "monto_apertura":        float(t.monto_apertura or 0),
        "monto_cierre_declarado": float(t.monto_cierre_declarado or 0),
        "monto_cierre_calculado": float(t.monto_cierre_calculado or 0),
        "diferencia":            float(t.diferencia or 0),
        "usuario_id":            t.usuario_id,
    } for t in turnos]