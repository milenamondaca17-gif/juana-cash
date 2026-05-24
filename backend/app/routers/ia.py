from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta, datetime
from ..database import get_db
from ..models.venta import Venta, ItemVenta
from ..models.producto import Producto

router = APIRouter(prefix="/ia", tags=["IA"])


# ─── 1. Venta cruzada ─────────────────────────────────────────────────────────

@router.get("/venta-cruzada/{producto_id}")
def venta_cruzada(producto_id: int, db: Session = Depends(get_db)):
    """
    Sugiere productos que se venden juntos con el producto dado.
    Analiza tickets donde aparece el producto y ve qué otros productos
    aparecen en esos mismos tickets.
    """
    # Encontrar ventas que tienen este producto
    ventas_con_producto = db.query(ItemVenta.venta_id).filter(
        ItemVenta.producto_id == producto_id
    ).subquery()

    # Contar co-ocurrencias con otros productos
    co_ocurrencias = db.query(
        ItemVenta.producto_id,
        func.count(ItemVenta.venta_id).label("veces_juntos")
    ).filter(
        ItemVenta.venta_id.in_(ventas_con_producto),
        ItemVenta.producto_id != producto_id,
        ItemVenta.producto_id != 0
    ).group_by(
        ItemVenta.producto_id
    ).order_by(
        func.count(ItemVenta.venta_id).desc()
    ).limit(5).all()

    resultado = []
    for co in co_ocurrencias:
        p = db.query(Producto).filter(Producto.id == co.producto_id).first()
        if p and p.activo:
            resultado.append({
                "id": p.id,
                "nombre": p.nombre,
                "precio_venta": float(p.precio_venta),
                "veces_juntos": co.veces_juntos,
            })

    return resultado


# ─── 2. Detección de anomalías ────────────────────────────────────────────────

@router.get("/anomalias")
def detectar_anomalias(db: Session = Depends(get_db)):
    """
    Detecta ventas anómalas: tickets muy por encima o por debajo del promedio.
    """
    hace_30 = date.today() - timedelta(days=30)
    ventas = db.query(Venta).filter(
        func.date(Venta.fecha) >= hace_30,
        Venta.estado == "completada"
    ).all()

    if len(ventas) < 5:
        return {"anomalias": [], "promedio": 0, "mensaje": "Pocas ventas para analizar"}

    totales = [float(v.total) for v in ventas]
    promedio = sum(totales) / len(totales)
    varianza = sum((x - promedio) ** 2 for x in totales) / len(totales)
    desvio = varianza ** 0.5

    umbral_alto = promedio + 2.5 * desvio
    umbral_bajo = promedio - 2.5 * desvio

    anomalias = []
    for v in ventas:
        total = float(v.total)
        if total > umbral_alto:
            tipo = "alta"
        elif total > 0 and total < umbral_bajo:
            tipo = "baja"
        else:
            continue

        anomalias.append({
            "id": v.id,
            "numero": v.numero,
            "total": total,
            "fecha": str(v.fecha)[:16],
            "tipo": tipo,
            "desviacion": round(abs(total - promedio) / desvio, 1) if desvio > 0 else 0
        })

    anomalias.sort(key=lambda x: x["desviacion"], reverse=True)

    return {
        "anomalias": anomalias[:10],
        "promedio": round(promedio, 2),
        "desvio": round(desvio, 2),
        "umbral_alto": round(umbral_alto, 2),
        "umbral_bajo": round(umbral_bajo, 2),
        "total_ventas_analizadas": len(ventas)
    }


# ─── 3. Precio dinámico sugerido ──────────────────────────────────────────────

@router.get("/precio-sugerido/{producto_id}")
def precio_sugerido(producto_id: int, margen_objetivo: float = 30.0,
                    db: Session = Depends(get_db)):
    """
    Sugiere el precio de venta para alcanzar el margen objetivo.
    También analiza si el precio actual está bien posicionado vs las ventas.
    """
    p = db.query(Producto).filter(Producto.id == producto_id).first()
    if not p:
        return {"error": "Producto no encontrado"}

    precio_costo = float(p.precio_costo) if p.precio_costo else 0
    precio_actual = float(p.precio_venta)

    # Precio sugerido por margen
    if precio_costo > 0:
        precio_por_margen = precio_costo / (1 - margen_objetivo / 100)
    else:
        precio_por_margen = None

    # Margen actual
    margen_actual = None
    if precio_costo > 0 and precio_actual > 0:
        margen_actual = ((precio_actual - precio_costo) / precio_actual) * 100

    # Velocidad de venta últimos 30 días
    hace_30 = date.today() - timedelta(days=30)
    vendido = db.query(func.sum(ItemVenta.cantidad)).join(Venta).filter(
        ItemVenta.producto_id == producto_id,
        func.date(Venta.fecha) >= hace_30,
        Venta.estado == "completada"
    ).scalar() or 0

    recomendacion = "ok"
    mensaje = "El precio está bien posicionado."

    if precio_por_margen:
        diferencia_pct = ((precio_actual - precio_por_margen) / precio_por_margen) * 100
        if diferencia_pct < -10:
            recomendacion = "subir"
            mensaje = f"El precio está {abs(diferencia_pct):.0f}% por debajo del margen objetivo."
        elif diferencia_pct > 20:
            recomendacion = "revisar"
            mensaje = f"El precio está {diferencia_pct:.0f}% por encima. Puede afectar ventas."

    return {
        "producto": p.nombre,
        "precio_actual": precio_actual,
        "precio_costo": precio_costo,
        "margen_actual": round(margen_actual, 1) if margen_actual else None,
        "margen_objetivo": margen_objetivo,
        "precio_sugerido": round(precio_por_margen, 2) if precio_por_margen else None,
        "vendido_30d": float(vendido),
        "recomendacion": recomendacion,
        "mensaje": mensaje
    }


# ─── 4. Comparativo semanal ───────────────────────────────────────────────────

@router.get("/comparativo-semanal")
def comparativo_semanal(db: Session = Depends(get_db)):
    """
    Compara la semana actual con la anterior en ventas, tickets y productos.
    """
    hoy = date.today()
    inicio_semana_actual = hoy - timedelta(days=hoy.weekday())
    inicio_semana_pasada = inicio_semana_actual - timedelta(days=7)
    fin_semana_pasada    = inicio_semana_actual - timedelta(days=1)

    def stats_semana(desde, hasta):
        ventas = db.query(Venta).filter(
            func.date(Venta.fecha) >= desde,
            func.date(Venta.fecha) <= hasta,
            Venta.estado == "completada"
        ).all()
        total = sum(float(v.total) for v in ventas)
        tickets = len(ventas)
        promedio = total / tickets if tickets > 0 else 0

        # Top producto
        items = db.query(
            ItemVenta.producto_id,
            func.sum(ItemVenta.subtotal).label("facturado")
        ).join(Venta).filter(
            func.date(Venta.fecha) >= desde,
            func.date(Venta.fecha) <= hasta,
            Venta.estado == "completada"
        ).group_by(ItemVenta.producto_id).order_by(
            func.sum(ItemVenta.subtotal).desc()
        ).first()

        top_producto = None
        if items:
            p = db.query(Producto).filter(Producto.id == items.producto_id).first()
            if p:
                top_producto = {"nombre": p.nombre, "facturado": float(items.facturado)}

        # Mejor día
        por_dia = {}
        for v in ventas:
            dia = str(v.fecha)[:10]
            por_dia[dia] = por_dia.get(dia, 0) + float(v.total)
        mejor_dia = max(por_dia, key=por_dia.get) if por_dia else None

        # Desglose por método
        from ..models.venta import Pago
        pagos = db.query(Pago).join(Venta).filter(
            func.date(Venta.fecha) >= desde,
            func.date(Venta.fecha) <= hasta,
            Venta.estado == "completada"
        ).all()
        metodos = {}
        for pg in pagos:
            metodos[pg.metodo] = metodos.get(pg.metodo, 0) + float(pg.monto)

        return {
            "total": round(total, 2),
            "tickets": tickets,
            "promedio_ticket": round(promedio, 2),
            "top_producto": top_producto,
            "mejor_dia": mejor_dia,
            "metodos": metodos
        }

    actual  = stats_semana(inicio_semana_actual, hoy)
    pasada  = stats_semana(inicio_semana_pasada, fin_semana_pasada)

    def variacion(a, b):
        if b == 0:
            return None
        return round(((a - b) / b) * 100, 1)

    dias_semana = hoy.weekday() + 1  # días transcurridos esta semana

    return {
        "semana_actual": {**actual, "desde": str(inicio_semana_actual), "hasta": str(hoy)},
        "semana_pasada": {**pasada, "desde": str(inicio_semana_pasada), "hasta": str(fin_semana_pasada)},
        "variacion_total":   variacion(actual["total"],   pasada["total"]),
        "variacion_tickets": variacion(actual["tickets"], pasada["tickets"]),
        "variacion_promedio": variacion(actual["promedio_ticket"], pasada["promedio_ticket"]),
        "dias_transcurridos": dias_semana,
        "proyeccion_semanal": round(actual["total"] / dias_semana * 7, 2) if dias_semana > 0 else 0
    }


# ─── 5. Insights del día ─────────────────────────────────────────────────────

@router.get("/insights-hoy")
def insights_hoy(db: Session = Depends(get_db)):
    """Resumen inteligente del día actual: comparativa, proyección, alertas y estrella."""
    hoy        = date.today()
    ahora      = datetime.now()
    hora_actual = ahora.hour
    mismo_dia  = hoy - timedelta(days=7)

    ventas_hoy = db.query(Venta).filter(
        func.date(Venta.fecha) == hoy, Venta.estado == "completada"
    ).all()
    total_hoy    = sum(float(v.total) for v in ventas_hoy)
    tickets_hoy  = len(ventas_hoy)
    promedio_hoy = total_hoy / tickets_hoy if tickets_hoy else 0

    ventas_semana = db.query(Venta).filter(
        func.date(Venta.fecha) == mismo_dia, Venta.estado == "completada"
    ).all()
    total_semana = sum(float(v.total) for v in ventas_semana)
    variacion_semanal = (
        round((total_hoy - total_semana) / total_semana * 100, 1)
        if total_semana > 0 else None
    )

    horas_hoy = {}
    for v in ventas_hoy:
        h = v.fecha.hour
        horas_hoy[h] = horas_hoy.get(h, 0) + 1
    hora_pico_hoy    = max(horas_hoy, key=horas_hoy.get) if horas_hoy else None
    tickets_hora_pico = horas_hoy.get(hora_pico_hoy, 0) if hora_pico_hoy is not None else 0

    top_item = db.query(
        ItemVenta.producto_id,
        func.sum(ItemVenta.subtotal).label("total"),
        func.sum(ItemVenta.cantidad).label("cantidad")
    ).join(Venta).filter(
        func.date(Venta.fecha) == hoy,
        Venta.estado == "completada",
        ItemVenta.producto_id != 0
    ).group_by(ItemVenta.producto_id).order_by(func.sum(ItemVenta.subtotal).desc()).first()

    producto_estrella = None
    if top_item:
        p = db.query(Producto).filter(Producto.id == top_item.producto_id).first()
        if p:
            producto_estrella = {
                "nombre":   p.nombre,
                "total":    round(float(top_item.total), 2),
                "cantidad": int(float(top_item.cantidad))
            }

    top_vendidos = db.query(
        ItemVenta.producto_id,
        func.sum(ItemVenta.cantidad).label("cantidad")
    ).join(Venta).filter(
        func.date(Venta.fecha) == hoy,
        Venta.estado == "completada",
        ItemVenta.producto_id != 0
    ).group_by(ItemVenta.producto_id).order_by(func.sum(ItemVenta.cantidad).desc()).limit(15).all()

    alertas = []
    for item in top_vendidos:
        p = db.query(Producto).filter(Producto.id == item.producto_id).first()
        if p and p.stock_actual is not None and p.stock_minimo is not None:
            stock_a = float(p.stock_actual)
            stock_m = float(p.stock_minimo)
            if stock_m > 0 and stock_a <= stock_m * 1.5:
                alertas.append({
                    "nombre":       p.nombre,
                    "stock_actual": round(stock_a, 1),
                    "stock_minimo": round(stock_m, 1),
                    "vendido_hoy":  int(float(item.cantidad))
                })

    proyeccion = None
    if hora_actual >= 8 and total_hoy > 0:
        horas_desde_apertura = max(1, hora_actual - 7)
        horas_hasta_cierre   = max(0, 22 - hora_actual)
        ritmo_hora = total_hoy / horas_desde_apertura
        proyeccion = round(total_hoy + ritmo_hora * horas_hasta_cierre, 2)

    return {
        "total_hoy":                    round(total_hoy, 2),
        "tickets_hoy":                  tickets_hoy,
        "promedio_hoy":                 round(promedio_hoy, 2),
        "total_mismo_dia_semana":       round(total_semana, 2),
        "variacion_vs_semana":          variacion_semanal,
        "hora_pico_hoy":                hora_pico_hoy,
        "tickets_hora_pico":            tickets_hora_pico,
        "producto_estrella":            producto_estrella,
        "alertas_stock":                alertas[:5],
        "proyeccion_dia":               proyeccion,
    }


# ─── 6. Resumen IA completo (para dashboard) ─────────────────────────────────

@router.get("/resumen")
def resumen_ia(db: Session = Depends(get_db)):
    """Datos resumidos de IA para mostrar en el dashboard."""
    # Anomalías recientes
    anomalias_data = detectar_anomalias(db)
    n_anomalias = len(anomalias_data.get("anomalias", []))

    # Productos críticos de stock
    criticos = db.query(Producto).filter(
        Producto.activo == True,
        Producto.stock_actual <= Producto.stock_minimo
    ).count()

    return {
        "anomalias_detectadas": n_anomalias,
        "productos_stock_critico": criticos,
    }
