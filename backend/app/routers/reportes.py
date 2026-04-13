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
    tickets_hoy = db.query(func.count(Venta.id)).filter(func.date(Venta.fecha) == hoy, Venta.estado == "completada").scalar() or 0
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    tickets_semana = db.query(func.count(Venta.id)).filter(func.date(Venta.fecha) >= inicio_semana, Venta.estado == "completada").scalar() or 0
    inicio_semana_pasada = inicio_semana - timedelta(days=7)
    fin_semana_pasada = inicio_semana - timedelta(days=1)
    tickets_semana_pasada = db.query(func.count(Venta.id)).filter(func.date(Venta.fecha) >= inicio_semana_pasada, func.date(Venta.fecha) <= fin_semana_pasada, Venta.estado == "completada").scalar() or 0
    inicio_mes = hoy.replace(day=1)
    tickets_mes = db.query(func.count(Venta.id)).filter(func.date(Venta.fecha) >= inicio_mes, Venta.estado == "completada").scalar() or 0
    if hoy.month == 1:
        inicio_mes_pasado = hoy.replace(year=hoy.year-1, month=12, day=1)
    else:
        inicio_mes_pasado = hoy.replace(month=hoy.month-1, day=1)
    fin_mes_pasado = inicio_mes - timedelta(days=1)
    tickets_mes_pasado = db.query(func.count(Venta.id)).filter(func.date(Venta.fecha) >= inicio_mes_pasado, func.date(Venta.fecha) <= fin_mes_pasado, Venta.estado == "completada").scalar() or 0
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