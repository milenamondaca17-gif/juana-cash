from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from datetime import datetime, date, timedelta
from typing import Optional, List
from ..database import get_db
from ..models.caja_turno import CajaTurno
from ..models.caja_aporte import CajaAporte
from ..models.venta import Venta

router = APIRouter(prefix="/caja", tags=["Caja"])

class AbrirCajaSchema(BaseModel):
    usuario_id: int
    monto_apertura: float = 0

class AporteSchema(BaseModel):
    turno_id: int
    monto: float
    descripcion: Optional[str] = "Aporte de caja"

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
        estado="abierto",
        apertura=datetime.now()
    )
    db.add(turno)
    db.commit()
    db.refresh(turno)
    return {"id": turno.id, "mensaje": "Caja abierta", "monto_apertura": datos.monto_apertura}

@router.post("/cerrar/{turno_id}")
def cerrar_caja(turno_id: int, datos: CerrarCajaSchema, db: Session = Depends(get_db)):
    import json
    from ..models.gasto import Gasto

    turno = db.query(CajaTurno).filter(CajaTurno.id == turno_id).first()
    if not turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado")

    ventas_turno = db.query(Venta).filter(
        Venta.fecha >= turno.apertura,
        Venta.usuario_id == turno.usuario_id,
        Venta.estado == "completada"
    ).all()

    # Total vendido (todos los métodos) — para columna "Vendido $" del historial
    total_vendido = sum(float(v.total) for v in ventas_turno)

    # Efectivo real de ventas (solo pagos en efectivo)
    efectivo_ventas = 0.0
    for v in ventas_turno:
        if v.pagos:
            for p in v.pagos:
                if p.metodo == "efectivo":
                    efectivo_ventas += float(p.monto or 0)
        elif getattr(v, "metodo_pago", None) == "efectivo":
            efectivo_ventas += float(v.total or 0)

    # Gastos del turno (desde apertura)
    gastos_hoy = db.query(Gasto).filter(
        Gasto.fecha >= turno.apertura,
        Gasto.usuario_id == turno.usuario_id
    ).all()
    total_gastos = sum(float(g.monto) for g in gastos_hoy)

    # Aportes de caja del turno
    aportes_turno = db.query(CajaAporte).filter(
        CajaAporte.turno_id == turno_id
    ).all()
    total_aportes = sum(float(a.monto) for a in aportes_turno)

    # Pagos de empleados del cierre
    pagos_emp = datos.pagos_empleados or []
    total_empleados = sum(p.monto for p in pagos_emp)

    # Efectivo esperado = apertura + aportes + efectivo ventas - gastos - empleados
    monto_apertura = float(turno.monto_apertura or 0)
    efectivo_esperado = monto_apertura + total_aportes + efectivo_ventas - total_gastos - total_empleados

    # Diferencia: lo que declaró el cajero vs lo que debería haber
    diferencia = datos.monto_cierre - efectivo_esperado

    turno.cierre                 = datetime.now()
    turno.monto_cierre_declarado = datos.monto_cierre
    turno.monto_cierre_calculado = total_vendido
    turno.diferencia             = diferencia
    turno.estado                 = "cerrado"
    turno.pagos_empleados        = json.dumps([{"nombre": p.nombre, "monto": p.monto} for p in pagos_emp])
    turno.total_empleados        = total_empleados

    db.commit()
    return {
        "mensaje":           "Caja cerrada",
        "total_vendido":     total_vendido,
        "efectivo_ventas":   efectivo_ventas,
        "total_gastos":      total_gastos,
        "total_aportes":     total_aportes,
        "efectivo_esperado": efectivo_esperado,
        "diferencia":        diferencia,
        "total_empleados":   total_empleados,
        "pagos_empleados":   [{"nombre": p.nombre, "monto": p.monto} for p in pagos_emp],
    }

@router.post("/aporte")
def registrar_aporte(datos: AporteSchema, db: Session = Depends(get_db)):
    turno = db.query(CajaTurno).filter(CajaTurno.id == datos.turno_id, CajaTurno.estado == "abierto").first()
    if not turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado o cerrado")
    if datos.monto <= 0:
        raise HTTPException(status_code=400, detail="El monto debe ser mayor a cero")
    aporte = CajaAporte(turno_id=datos.turno_id, monto=datos.monto, descripcion=datos.descripcion)
    db.add(aporte)
    db.commit()
    db.refresh(aporte)
    return {"id": aporte.id, "monto": aporte.monto, "descripcion": aporte.descripcion}

@router.get("/aportes/{turno_id}")
def aportes_turno(turno_id: int, db: Session = Depends(get_db)):
    aportes = db.query(CajaAporte).filter(CajaAporte.turno_id == turno_id).order_by(CajaAporte.fecha).all()
    total = sum(float(a.monto) for a in aportes)
    return {
        "aportes": [{"id": a.id, "monto": float(a.monto), "descripcion": a.descripcion,
                     "hora": a.fecha.strftime("%H:%M")} for a in aportes],
        "total": total
    }

@router.get("/turno-actual/{usuario_id}")
def turno_actual(usuario_id: int, db: Session = Depends(get_db)):
    turno = db.query(CajaTurno).filter(
        CajaTurno.usuario_id == usuario_id,
        CajaTurno.estado == "abierto"
    ).first()
    if not turno:
        return {"abierto": False}
    return {"abierto": True, "id": turno.id, "monto_apertura": float(turno.monto_apertura),
            "apertura": str(turno.apertura)[:16] if turno.apertura else ""}

@router.get("/historial")
def historial_cierres(limite: int = 30, db: Session = Depends(get_db)):
    from ..models.venta import Pago
    from ..models.gasto import Gasto
    from ..models.caja_aporte import CajaAporte
    from ..models.usuario import Usuario

    turnos = db.query(CajaTurno).filter(
        CajaTurno.estado == "cerrado"
    ).order_by(CajaTurno.cierre.desc()).limit(limite).all()

    resultado = []
    for t in turnos:
        hasta = t.cierre or datetime.now()

        # Ventas completadas del turno
        ventas = db.query(Venta).filter(
            Venta.fecha >= t.apertura,
            Venta.fecha <= hasta,
            Venta.estado == "completada"
        ).all()
        ids_ventas = [v.id for v in ventas]

        # Desglose por método de pago
        desglose = {"efectivo": 0.0, "debito": 0.0, "tarjeta": 0.0,
                    "mercadopago_qr": 0.0, "transferencia": 0.0, "fiado": 0.0}
        if ids_ventas:
            pagos = db.query(Pago).filter(Pago.venta_id.in_(ids_ventas)).all()
            for p in pagos:
                m = p.metodo.lower()
                if m in desglose:
                    desglose[m] += float(p.monto or 0)

        # Gastos y aportes del turno
        total_gastos = sum(float(g.monto) for g in db.query(Gasto).filter(
            Gasto.fecha >= t.apertura, Gasto.fecha <= hasta).all())
        total_aportes = sum(float(a.monto) for a in db.query(CajaAporte).filter(
            CajaAporte.turno_id == t.id).all())

        # Nombre del cajero
        usuario = db.query(Usuario).filter(Usuario.id == t.usuario_id).first()
        nombre_cajero = usuario.nombre if usuario else f"Usuario {t.usuario_id}"

        resultado.append({
            "id":                     t.id,
            "apertura":               str(t.apertura)[:16] if t.apertura else "",
            "cierre":                 str(t.cierre)[:16] if t.cierre else "",
            "cajero":                 nombre_cajero,
            "monto_apertura":         float(t.monto_apertura or 0),
            "total_aportes":          total_aportes,
            "monto_cierre_declarado": float(t.monto_cierre_declarado or 0),
            "monto_cierre_calculado": float(t.monto_cierre_calculado or 0),
            "diferencia":             float(t.diferencia or 0),
            "total_gastos":           total_gastos,
            "efectivo":               desglose["efectivo"],
            "debito":                 desglose["debito"],
            "tarjeta":                desglose["tarjeta"],
            "mercadopago_qr":         desglose["mercadopago_qr"],
            "transferencia":          desglose["transferencia"],
            "fiado":                  desglose["fiado"],
            "cantidad_ventas":        len(ventas),
        })
    return resultado

@router.get("/resumen-rapido")
def resumen_rapido(usuario_id: int = 1, db: Session = Depends(get_db)):
    """
    Devuelve en una sola llamada todo lo necesario para la pantalla Caja del móvil:
    hoy, ayer, semana, mes y estado del turno actual.
    """
    from collections import defaultdict

    hoy  = date.today()
    ayer = hoy - timedelta(days=1)
    sem  = hoy - timedelta(days=7)
    mes  = hoy.replace(day=1)

    def _agrupar(ventas):
        tots = defaultdict(float)
        total = 0.0
        cantidad = 0
        for v in ventas:
            if v.estado != "completada":
                continue
            cantidad += 1
            total += float(v.total or 0)
            if hasattr(v, "pagos") and v.pagos:
                for p in v.pagos:
                    tots[p.metodo.lower()] += float(p.monto or 0)
            elif getattr(v, "metodo_pago", None):
                tots[v.metodo_pago.lower()] += float(v.total or 0)
        ticket = total / cantidad if cantidad else 0
        return {
            "efectivo":       round(tots.get("efectivo", 0), 2),
            "debito":         round(tots.get("debito", 0), 2),
            "tarjeta":        round(tots.get("tarjeta", 0), 2),
            "mercadopago_qr": round(tots.get("mercadopago_qr", 0), 2),
            "transferencia":  round(tots.get("transferencia", 0), 2),
            "fiado":          round(tots.get("fiado", 0), 2),
            "total":          round(total, 2),
            "cantidad":       cantidad,
            "ticket_promedio": round(ticket, 2),
        }

    ventas_hoy  = db.query(Venta).filter(func.date(Venta.fecha) == hoy).all()
    ventas_ayer = db.query(Venta).filter(func.date(Venta.fecha) == ayer).all()
    ventas_sem  = db.query(Venta).filter(func.date(Venta.fecha) >= sem).all()
    ventas_mes  = db.query(Venta).filter(func.date(Venta.fecha) >= mes).all()

    turno = db.query(CajaTurno).filter(
        CajaTurno.usuario_id == usuario_id,
        CajaTurno.estado == "abierto"
    ).first()

    hoy_data  = _agrupar(ventas_hoy)
    ayer_data = _agrupar(ventas_ayer)

    delta_pct = 0.0
    if ayer_data["total"] > 0:
        delta_pct = round((hoy_data["total"] - ayer_data["total"]) / ayer_data["total"] * 100, 1)

    return {
        "hoy":   hoy_data,
        "ayer":  ayer_data,
        "delta_pct": delta_pct,
        "semana": _agrupar(ventas_sem),
        "mes":    _agrupar(ventas_mes),
        "turno":  {
            "abierto":        turno is not None,
            "id":             turno.id            if turno else None,
            "apertura":       str(turno.apertura)[:16] if turno else None,
            "monto_apertura": float(turno.monto_apertura) if turno else 0,
        }
    }


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
        "efectivo": 0, "debito": 0, "tarjeta": 0,
        "mercadopago_qr": 0, "transferencia": 0,
        "fiado": 0, "total": 0, "cantidad": 0
    })

    for v in ventas:
        dia = str(v.fecha)[:10]
        por_dia[dia]["total"] += float(v.total or 0)
        por_dia[dia]["cantidad"] += 1
        if hasattr(v, "pagos") and v.pagos:
            for p in v.pagos:
                m = p.metodo.lower()
                if m in por_dia[dia]:
                    por_dia[dia][m] += float(p.monto or 0)
        elif getattr(v, "metodo_pago", None):
            m = v.metodo_pago.lower()
            if m in por_dia[dia]:
                por_dia[dia][m] += float(v.total or 0)

    resultado = []
    for dia in sorted(por_dia.keys(), reverse=True):
        d = por_dia[dia]
        cant = d["cantidad"]
        resultado.append({
            "fecha":           dia,
            "efectivo":        round(d["efectivo"], 2),
            "debito":          round(d["debito"], 2),
            "tarjeta":         round(d["tarjeta"], 2),
            "mercadopago_qr":  round(d["mercadopago_qr"], 2),
            "transferencia":   round(d["transferencia"], 2),
            "fiado":           round(d["fiado"], 2),
            "total":           round(d["total"], 2),
            "cantidad":        cant,
            "ticket_promedio": round(d["total"] / cant, 2) if cant else 0,
        })

    return resultado
