from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import date, timedelta
from ..database import get_db
from ..models.venta import Venta, ItemVenta, Pago
from ..models.producto import Producto, Categoria
from .. import models

router = APIRouter(prefix="/reportes", tags=["Reportes"])

def reporte_por_fechas(db, desde, hasta=None):
    query = db.query(Venta).filter(func.date(Venta.fecha) >= desde)
    if hasta:
        query = query.filter(func.date(Venta.fecha) <= hasta)
    ventas = query.order_by(Venta.fecha.desc()).all()
    total = sum(float(v.total) for v in ventas if v.estado == "completada")
    def _fmt_fecha(f):
        """Devuelve siempre 'YYYY-MM-DD HH:MM:SS' sin microsegundos."""
        if f is None:
            return ""
        try:
            # Si ya es datetime object
            if hasattr(f, 'strftime'):
                return f.strftime("%Y-%m-%d %H:%M:%S")
            # Si es string, limpiar microsegundos y T
            s = str(f).replace("T", " ")
            return s[:19]  # tomar solo YYYY-MM-DD HH:MM:SS
        except Exception:
            return str(f)[:19]

    return {
        "cantidad_ventas": len([v for v in ventas if v.estado == "completada"]),
        "total_vendido": total,
        "ventas": [
            {
                "id": v.id,
                "numero": v.numero,
                "total": float(v.total),
                "estado": v.estado,
                "origen": (getattr(v, 'origen', None) or 'mostrador'),
                "metodo_pago": (
                    v.pagos[0].metodo if v.pagos
                    else (getattr(v, 'metodo_pago', None) or 'efectivo')
                ).lower(),
                "metodo_secundario": v.pagos[1].metodo if v.pagos and len(v.pagos) > 1 else None,
                "monto_secundario": float(v.pagos[1].monto) if v.pagos and len(v.pagos) > 1 else 0.0,
                "fecha": _fmt_fecha(v.fecha)
            }
            for v in ventas
        ]
    }

@router.get("/hoy")
def reporte_hoy(db: Session = Depends(get_db)):
    hoy = date.today()
    datos = reporte_por_fechas(db, hoy)
    datos["fecha"] = str(hoy)
    pagos_hoy = db.query(Pago).join(Venta).filter(
        func.date(Venta.fecha) == hoy,
        Venta.estado == "completada"
    ).all()
    desglose = {}
    for p in pagos_hoy:
        m = p.metodo
        desglose[m] = desglose.get(m, 0.0) + float(p.monto)
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

@router.get("/rango")
def reporte_rango(desde: str, hasta: str, db: Session = Depends(get_db)):
    """Reporte por rango de fechas personalizado. Formato: YYYY-MM-DD"""
    try:
        desde_date = date.fromisoformat(desde)
        hasta_date = date.fromisoformat(hasta)
    except ValueError:
        desde_date = date.today()
        hasta_date = date.today()
    datos = reporte_por_fechas(db, desde_date, hasta_date)
    datos["desde"] = str(desde_date)
    datos["hasta"] = str(hasta_date)
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

@router.get("/productos-por-fecha")
def productos_por_fecha(desde: str, hasta: str, db: Session = Depends(get_db)):
    """Todos los productos vendidos en un rango de fechas, ordenados por cantidad."""
    try:
        desde_date = date.fromisoformat(desde)
        hasta_date = date.fromisoformat(hasta)
    except ValueError:
        desde_date = date.today()
        hasta_date = date.today()

    resultados = db.query(
        Producto.nombre,
        Producto.codigo_barra,
        func.sum(ItemVenta.cantidad).label("total_vendido"),
        func.sum(ItemVenta.subtotal).label("total_facturado"),
        func.count(ItemVenta.venta_id).label("cantidad_tickets")
    ).join(ItemVenta, Producto.id == ItemVenta.producto_id)\
     .join(Venta, ItemVenta.venta_id == Venta.id)\
     .filter(
         func.date(Venta.fecha) >= desde_date,
         func.date(Venta.fecha) <= hasta_date,
         Venta.estado == "completada"
     )\
     .group_by(Producto.id)\
     .order_by(func.sum(ItemVenta.cantidad).desc())\
     .all()

    return [
        {
            "nombre":    r.nombre,
            "codigo":    r.codigo_barra or "",
            "cantidad":  float(r.total_vendido),
            "facturado": float(r.total_facturado),
            "tickets":   int(r.cantidad_tickets)
        }
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

@router.get("/horario-pico")
def horario_pico(db: Session = Depends(get_db)):
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
    hoy = date.today()
    ventas_hoy = db.query(Venta).filter(func.date(Venta.fecha) == hoy, Venta.estado == "completada").all()
    total_hoy = sum(float(v.total) for v in ventas_hoy)
    tickets_hoy = len(ventas_hoy)
    promedio = (total_hoy / tickets_hoy) if tickets_hoy > 0 else 0
    
    ayer = hoy - timedelta(days=1)
    ventas_ayer = db.query(Venta).filter(func.date(Venta.fecha) == ayer, Venta.estado == "completada").all()
    total_ayer = sum(float(v.total) for v in ventas_ayer)

    pagos_hoy = db.query(Pago).join(Venta).filter(func.date(Venta.fecha) == hoy, Venta.estado == "completada").all()
    desglose = {}
    for p in pagos_hoy:
        m = p.metodo
        desglose[m] = desglose.get(m, 0.0) + float(p.monto)

    inicio_anio = hoy.replace(month=1, day=1)
    CATEGORIAS_EXCLUIR = ["carniceria", "carnicería", "fiamberia", "fiambería",
                          "lacteos", "lácteos", "fiambreria", "fiambrerìa"]
    top_productos = db.query(
        Producto.nombre,
        func.sum(ItemVenta.cantidad).label("qty"),
        func.sum(ItemVenta.subtotal).label("total")
    ).join(ItemVenta).join(Venta)\
     .outerjoin(Categoria, Producto.categoria_id == Categoria.id)\
     .filter(
        func.date(Venta.fecha) >= inicio_anio,
        Venta.estado == "completada",
        ~func.lower(func.coalesce(Categoria.nombre, "")).in_(CATEGORIAS_EXCLUIR)
    ).group_by(Producto.id).order_by(func.sum(ItemVenta.subtotal).desc()).limit(15).all()

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
        "top_productos": [{"nombre": r.nombre, "cantidad": float(r.qty), "total": float(r.total)} for r in top_productos]
    }

@router.get("/ventas-periodo")
def ventas_por_periodo(periodo: str = "dia", db: Session = Depends(get_db)):
    if periodo == "mes":
        formato = "%Y-%m"
    elif periodo == "semana":
        formato = "%Y-%W"
    else:
        formato = "%Y-%m-%d"

    query = db.query(
        func.strftime(formato, Venta.fecha).label("periodo"),
        Producto.nombre,
        func.sum(ItemVenta.cantidad),
        func.sum(ItemVenta.precio_unitario * ItemVenta.cantidad)
    ).join(ItemVenta, Venta.id == ItemVenta.venta_id)\
     .join(Producto, ItemVenta.producto_id == Producto.id)\
     .filter(Venta.estado == "completada")\
     .group_by("periodo", Producto.id)\
     .order_by(desc("periodo"))\
     .all()

    return [
        {"fecha": r[0], "producto": r[1], "cantidad": float(r[2]), "total": float(r[3])}
        for r in query
    ]