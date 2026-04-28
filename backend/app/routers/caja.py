from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from datetime import datetime, date, timedelta
from typing import Optional, List
from ..database import get_db
from ..models.caja_turno import CajaTurno
from ..models.venta import Venta

router = APIRouter(prefix="/caja", tags=["Caja"])

class AbrirCajaSchema(BaseModel):
    usuario_id: int
    monto_apertura: float = 0

class PagoEmpleado(BaseModel):
    nombre: str
    monto: float

class CerrarCajaSchema(BaseModel):
    monto_cierre: float = 0
    pagos_empleados: Optional[List[PagoEmpleado]] = []

@router.post("/abrir")
def abrir_caja(datos: AbrirCajaSchema, db: Session = Depends(get_db)):
    turno_abierto = db.query(CajaTurno).filter(
        CajaTurno.usuario_id == datos.usuario_id,
        CajaTurno.estado == "abierto"
    ).first()
    if turno_abierto:
        return {"id": turno_abierto.id, "mensaje": "Ya hay una caja abierta"}
    turno = CajaTurno(
        usuario_id=datos.usuario_id,
        monto_apertura=datos.monto_apertura,
        estado="abierto"
    )
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

    # Guardar pagos de empleados como JSON en el turno
    import json
    pagos_emp = datos.pagos_empleados or []
    total_empleados = sum(p.monto for p in pagos_emp)

    turno.cierre = datetime.now()
    turno.monto_cierre_declarado = datos.monto_cierre
    turno.monto_cierre_calculado = total_calculado
    turno.diferencia = diferencia
    turno.estado = "cerrado"

    # Guardar pagos empleados si el modelo lo soporta
    try:
        turno.pagos_empleados = json.dumps([{"nombre": p.nombre, "monto": p.monto} for p in pagos_emp])
        turno.total_empleados = total_empleados
    except Exception:
        pass

    db.commit()
    return {
        "mensaje": "Caja cerrada",
        "total_calculado": total_calculado,
        "diferencia": diferencia,
        "total_empleados": total_empleados,
        "pagos_empleados": [{"nombre": p.nombre, "monto": p.monto} for p in pagos_emp]
    }

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
        "id":                     t.id,
        "apertura":               str(t.apertura)[:16] if t.apertura else "",
        "cierre":                 str(t.cierre)[:16] if t.cierre else "",
        "monto_apertura":         float(t.monto_apertura or 0),
        "monto_cierre_declarado": float(t.monto_cierre_declarado or 0),
        "monto_cierre_calculado": float(t.monto_cierre_calculado or 0),
        "diferencia":             float(t.diferencia or 0),
        "usuario_id":             t.usuario_id,
    } for t in turnos]

@router.get("/historial-efectivo")
def historial_efectivo(dias: int = 30, db: Session = Depends(get_db)):
    """
    Devuelve el total de efectivo vendido por día en los últimos N días.
    Útil para ver la acumulación día a día.
    """
    desde = date.today() - timedelta(days=dias)
    ventas = db.query(Venta).filter(
        func.date(Venta.fecha) >= desde,
        Venta.estado == "completada"
    ).all()

    # Agrupar por fecha y método
    from collections import defaultdict
    por_dia = defaultdict(lambda: {
        "efectivo": 0, "tarjeta": 0,
        "mercadopago_qr": 0, "transferencia": 0,
        "fiado": 0, "total": 0
    })

    for v in ventas:
        dia = str(v.fecha)[:10]
        metodo = str(v.metodo_pago or "efectivo").lower()
        monto = float(v.total or 0)
        if metodo in por_dia[dia]:
            por_dia[dia][metodo] += monto
        por_dia[dia]["total"] += monto

    # Ordenar por fecha descendente
    resultado = []
    for dia in sorted(por_dia.keys(), reverse=True):
        d = por_dia[dia]
        resultado.append({
            "fecha": dia,
            "efectivo":       round(d["efectivo"], 2),
            "tarjeta":        round(d["tarjeta"], 2),
            "mercadopago_qr": round(d["mercadopago_qr"], 2),
            "transferencia":  round(d["transferencia"], 2),
            "fiado":          round(d["fiado"], 2),
            "total":          round(d["total"], 2),
        })

    return resultado
