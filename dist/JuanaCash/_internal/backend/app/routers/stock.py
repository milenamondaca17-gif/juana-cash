from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta, datetime
from pydantic import BaseModel
from typing import Optional
from ..database import get_db
from ..models.producto import Producto
from ..models.venta import Venta, ItemVenta

router = APIRouter(prefix="/stock", tags=["Stock"])


# ─── Predicción de stock ──────────────────────────────────────────────────────

@router.get("/prediccion")
def prediccion_stock(db: Session = Depends(get_db)):
    """
    Para cada producto, calcula cuántos días de stock quedan
    basándose en la velocidad de venta de los últimos 30 días.
    """
    hace_30 = date.today() - timedelta(days=30)

    # Ventas por producto en últimos 30 días
    ventas_mes = db.query(
        ItemVenta.producto_id,
        func.sum(ItemVenta.cantidad).label("vendido")
    ).join(Venta).filter(
        func.date(Venta.fecha) >= hace_30,
        Venta.estado == "completada"
    ).group_by(ItemVenta.producto_id).all()

    vendido_por_id = {v.producto_id: float(v.vendido) for v in ventas_mes}

    productos = db.query(Producto).filter(Producto.activo == True).all()
    resultado = []
    for p in productos:
        stock = float(p.stock_actual)
        vendido = vendido_por_id.get(p.id, 0)
        velocidad_diaria = vendido / 30 if vendido > 0 else 0

        if velocidad_diaria > 0:
            dias_restantes = int(stock / velocidad_diaria)
        elif stock == 0:
            dias_restantes = 0
        else:
            dias_restantes = 999  # sin ventas recientes

        alerta = None
        if dias_restantes == 0:
            alerta = "sin_stock"
        elif dias_restantes <= 3:
            alerta = "critico"
        elif dias_restantes <= 7:
            alerta = "bajo"
        elif dias_restantes <= 15:
            alerta = "moderado"

        resultado.append({
            "id": p.id,
            "nombre": p.nombre,
            "codigo_barra": p.codigo_barra or "",
            "stock_actual": stock,
            "stock_minimo": float(p.stock_minimo),
            "vendido_30d": vendido,
            "velocidad_diaria": round(velocidad_diaria, 2),
            "dias_restantes": dias_restantes,
            "alerta": alerta,
            "precio_costo": float(p.precio_costo) if p.precio_costo else 0,
        })

    # Ordenar: primero los críticos
    orden = {"sin_stock": 0, "critico": 1, "bajo": 2, "moderado": 3, None: 4}
    resultado.sort(key=lambda x: (orden.get(x["alerta"], 4), x["dias_restantes"]))
    return resultado


# ─── Alerta de stock bajo (para sidebar al iniciar) ──────────────────────────

@router.get("/alertas-criticas")
def alertas_criticas(db: Session = Depends(get_db)):
    """Productos con stock <= stock_minimo. Rápido, sin cálculos de velocidad."""
    productos = db.query(Producto).filter(
        Producto.activo == True,
        Producto.stock_actual <= Producto.stock_minimo
    ).order_by(Producto.stock_actual.asc()).all()

    return [
        {
            "id": p.id,
            "nombre": p.nombre,
            "stock_actual": float(p.stock_actual),
            "stock_minimo": float(p.stock_minimo),
        }
        for p in productos
    ]


# ─── Inventario rápido ────────────────────────────────────────────────────────

class AjusteStock(BaseModel):
    producto_id: int
    stock_nuevo: float
    motivo: Optional[str] = "Inventario rápido"

@router.post("/ajuste")
def ajuste_stock(datos: AjusteStock, db: Session = Depends(get_db)):
    """Ajusta el stock de un producto manualmente."""
    p = db.query(Producto).filter(Producto.id == datos.producto_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    stock_anterior = float(p.stock_actual)
    p.stock_actual = datos.stock_nuevo
    db.commit()
    db.refresh(p)
    return {
        "ok": True,
        "nombre": p.nombre,
        "stock_anterior": stock_anterior,
        "stock_nuevo": float(p.stock_actual),
        "diferencia": datos.stock_nuevo - stock_anterior
    }


@router.post("/ajuste-masivo")
def ajuste_masivo(ajustes: list[AjusteStock], db: Session = Depends(get_db)):
    """Aplica múltiples ajustes de stock de una sola vez."""
    resultados = []
    for a in ajustes:
        p = db.query(Producto).filter(Producto.id == a.producto_id).first()
        if p:
            p.stock_actual = a.stock_nuevo
            resultados.append({"id": p.id, "nombre": p.nombre, "stock_nuevo": a.stock_nuevo})
    db.commit()
    return {"ok": True, "ajustados": len(resultados), "detalle": resultados}


# ─── Vencimientos ─────────────────────────────────────────────────────────────

@router.get("/vencimientos")
def vencimientos(db: Session = Depends(get_db)):
    """
    Productos con fecha_vencimiento próxima.
    Requiere que el modelo tenga fecha_vencimiento (columna opcional).
    Si no existe la columna, devuelve lista vacía.
    """
    try:
        hoy = date.today()
        productos = db.query(Producto).filter(
            Producto.activo == True,
            Producto.fecha_vencimiento != None,
            Producto.fecha_vencimiento <= hoy + timedelta(days=30)
        ).all()
        return [
            {
                "id": p.id,
                "nombre": p.nombre,
                "stock_actual": float(p.stock_actual),
                "fecha_vencimiento": str(p.fecha_vencimiento),
                "dias_para_vencer": (p.fecha_vencimiento - hoy).days
            }
            for p in productos
        ]
    except Exception:
        return []
