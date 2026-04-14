from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta
from ..database import get_db
from ..models.venta import Venta, ItemVenta
from ..models.producto import Producto

router = APIRouter(prefix="/reportes", tags=["Reportes"])

def reporte_por_fechas(db, desde, hasta=None):
    query = db.query(Venta).filter(func.date(Venta.fecha) >= desde)
    if hasta:
        query = query.filter(func.date(Venta.fecha) <= hasta)
    ventas = query.order_by(Venta.fecha.desc()).all()
    total = sum(float(v.total) for v in ventas if v.estado == "completada")
    return {
        "cantidad_ventas": len([v for v in ventas if v.estado == "completada"]),
        "total_vendido": total,
        "ventas": [
            {
                "id": v.id,
                "numero": v.numero,
                "total": float(v.total),
                "estado": v.estado,
                "metodo_pago": v.pagos[0].metodo if v.pagos else "efectivo",
                "fecha": str(v.fecha)
            }
            for v in ventas
        ]
    }

@router.get("/hoy")
def reporte_hoy(db: Session = Depends(get_db)):
    hoy = date.today()
    datos = reporte_por_fechas(db, hoy)
    datos["fecha"] = str(hoy)
    # Desglose por método de pago
    from ..models.venta import Pago
    pagos_hoy = db.query(Pago).join(Venta).filter(
        func.date(Venta.fecha) == hoy,
        Venta.estado == "completada"
    ).all()
    desglose = {}
    for p in pagos_hoy:
        m = p.metodo
        if m not in desglose:
            desglose[m] = 0.0
        desglose[m] += float(p.monto)
    datos["desglose_metodos"] = desglose
    return datos

@router.get("/semana")
def reporte_semana(db: Session = Depends(get_db)):
    desde = date.today() - timedelta(days=7)
    datos = reporte_por_fechas(db, desde)
    datos["desde"] = str(desde)
    datos["hasta"] = str(date.today())
    return datos

@router.get("/mes")
def reporte_mes(db: Session = Depends(get_db)):
    hoy = date.today()
    desde = hoy.replace(day=1)
    datos = reporte_por_fechas(db, desde)
    datos["desde"] = str(desde)
    datos["hasta"] = str(hoy)
    return datos

@router.get("/anio")
def reporte_anio(db: Session = Depends(get_db)):
    hoy = date.today()
    desde = hoy.replace(month=1, day=1)
    datos = reporte_por_fechas(db, desde)
    datos["desde"] = str(desde)
    datos["hasta"] = str(hoy)
    return datos

@router.get("/productos-mas-vendidos")
def productos_mas_vendidos(db: Session = Depends(get_db)):
    resultados = db.query(
        Producto.nombre,
        func.sum(ItemVenta.cantidad).label("total_vendido"),
        func.sum(ItemVenta.subtotal).label("total_facturado")
    ).join(ItemVenta).group_by(Producto.id).order_by(
        func.sum(ItemVenta.cantidad).desc()
    ).limit(10).all()
    return [
        {"nombre": r.nombre, "cantidad": float(r.total_vendido), "facturado": float(r.total_facturado)}
        for r in resultados
    ]

@router.get("/stock-bajo")
def stock_bajo(db: Session = Depends(get_db)):
    productos = db.query(Producto).filter(
        Producto.stock_actual <= Producto.stock_minimo,
        Producto.activo == True
    ).all()
    return [
        {"id": p.id, "nombre": p.nombre, "stock_actual": float(p.stock_actual), "stock_minimo": float(p.stock_minimo)}
        for p in productos
    ]

@router.get("/conteo-tickets")
def conteo_tickets(db: Session = Depends(get_db)):
    hoy = date.today()
    tickets_hoy = db.query(func.count(Venta.id)).filter(
        func.date(Venta.fecha) == hoy, Venta.estado == "completada"
    ).scalar() or 0
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    tickets_semana = db.query(func.count(Venta.id)).filter(
        func.date(Venta.fecha) >= inicio_semana, Venta.estado == "completada"
    ).scalar() or 0
    inicio_semana_pasada = inicio_semana - timedelta(days=7)
    fin_semana_pasada = inicio_semana - timedelta(days=1)
    tickets_semana_pasada = db.query(func.count(Venta.id)).filter(
        func.date(Venta.fecha) >= inicio_semana_pasada,
        func.date(Venta.fecha) <= fin_semana_pasada,
        Venta.estado == "completada"
    ).scalar() or 0
    inicio_mes = hoy.replace(day=1)
    tickets_mes = db.query(func.count(Venta.id)).filter(
        func.date(Venta.fecha) >= inicio_mes, Venta.estado == "completada"
    ).scalar() or 0
    if hoy.month == 1:
        inicio_mes_pasado = hoy.replace(year=hoy.year - 1, month=12, day=1)
    else:
        inicio_mes_pasado = hoy.replace(month=hoy.month - 1, day=1)
    fin_mes_pasado = inicio_mes - timedelta(days=1)
    tickets_mes_pasado = db.query(func.count(Venta.id)).filter(
        func.date(Venta.fecha) >= inicio_mes_pasado,
        func.date(Venta.fecha) <= fin_mes_pasado,
        Venta.estado == "completada"
    ).scalar() or 0
    variacion_semana = tickets_semana - tickets_semana_pasada
    variacion_mes = tickets_mes - tickets_mes_pasado
    alerta_semana = None
    alerta_mes = None
    if tickets_semana_pasada > 0 and variacion_semana < 0:
        pct = abs(variacion_semana / tickets_semana_pasada * 100)
        alerta_semana = f"⚠️ Esta semana bajaron {abs(variacion_semana)} tickets vs semana pasada ({pct:.0f}% menos)"
    if tickets_mes_pasado > 0 and variacion_mes < 0:
        pct = abs(variacion_mes / tickets_mes_pasado * 100)
        alerta_mes = f"⚠️ Este mes bajaron {abs(variacion_mes)} tickets vs mes pasado ({pct:.0f}% menos)"
    return {
        "tickets_hoy": tickets_hoy,
        "tickets_semana": tickets_semana,
        "tickets_semana_pasada": tickets_semana_pasada,
        "tickets_mes": tickets_mes,
        "tickets_mes_pasado": tickets_mes_pasado,
        "variacion_semana": variacion_semana,
        "variacion_mes": variacion_mes,
        "alerta_semana": alerta_semana,
        "alerta_mes": alerta_mes,
    }

@router.get("/horario-pico")
def horario_pico(db: Session = Depends(get_db)):
    """Estadística de ventas agrupadas por hora del día."""
    ventas = db.query(Venta).filter(Venta.estado == "completada").all()
    horas = {}
    for v in ventas:
        try:
            hora = v.fecha.hour
            if hora not in horas:
                horas[hora] = {"ventas": 0, "total": 0.0}
            horas[hora]["ventas"] += 1
            horas[hora]["total"] += float(v.total)
        except Exception:
            continue
    resultado = []
    for hora in range(24):
        d = horas.get(hora, {"ventas": 0, "total": 0.0})
        resultado.append({
            "hora": hora,
            "label": f"{hora:02d}:00",
            "ventas": d["ventas"],
            "total": round(d["total"], 2)
        })
    return resultado

@router.get("/dashboard")
def dashboard_tiempo_real(db: Session = Depends(get_db)):
    """Datos completos para el dashboard del dueño."""
    hoy = date.today()

    # Ventas hoy
    ventas_hoy = db.query(Venta).filter(
        func.date(Venta.fecha) == hoy,
        Venta.estado == "completada"
    ).all()
    total_hoy = sum(float(v.total) for v in ventas_hoy)
    tickets_hoy = len(ventas_hoy)
    promedio = (total_hoy / tickets_hoy) if tickets_hoy > 0 else 0

    # Ventas ayer
    ayer = hoy - timedelta(days=1)
    ventas_ayer = db.query(Venta).filter(
        func.date(Venta.fecha) == ayer,
        Venta.estado == "completada"
    ).all()
    total_ayer = sum(float(v.total) for v in ventas_ayer)

    # Desglose métodos hoy
    from ..models.venta import Pago
    pagos_hoy = db.query(Pago).join(Venta).filter(
        func.date(Venta.fecha) == hoy,
        Venta.estado == "completada"
    ).all()
    desglose = {}
    for p in pagos_hoy:
        m = p.metodo
        desglose[m] = desglose.get(m, 0.0) + float(p.monto)

    # Top 5 productos del mes
    inicio_mes = hoy.replace(day=1)
    top_productos = db.query(
        Producto.nombre,
        func.sum(ItemVenta.cantidad).label("qty"),
        func.sum(ItemVenta.subtotal).label("total")
    ).join(ItemVenta).join(Venta).filter(
        func.date(Venta.fecha) >= inicio_mes,
        Venta.estado == "completada"
    ).group_by(Producto.id).order_by(
        func.sum(ItemVenta.subtotal).desc()
    ).limit(5).all()

    # Horario pico hoy
    horas_hoy = {}
    for v in ventas_hoy:
        try:
            hora = v.fecha.hour
            horas_hoy[hora] = horas_hoy.get(hora, 0) + 1
        except Exception:
            pass
    hora_pico = max(horas_hoy, key=horas_hoy.get) if horas_hoy else None

    # Variación vs ayer
    variacion_pct = 0
    if total_ayer > 0:
        variacion_pct = ((total_hoy - total_ayer) / total_ayer) * 100

    return {
        "total_hoy": round(total_hoy, 2),
        "total_ayer": round(total_ayer, 2),
        "variacion_pct": round(variacion_pct, 1),
        "tickets_hoy": tickets_hoy,
        "ticket_promedio": round(promedio, 2),
        "desglose_metodos": desglose,
        "metodo_mas_usado": max(desglose, key=desglose.get) if desglose else "efectivo",
        "top_productos": [
            {"nombre": r.nombre, "cantidad": float(r.qty), "total": float(r.total)}
            for r in top_productos
        ],
        "hora_pico": hora_pico,
        "horas_hoy": [
            {"hora": h, "label": f"{h:02d}:00", "ventas": horas_hoy.get(h, 0)}
            for h in range(6, 23)
        ]
    }
