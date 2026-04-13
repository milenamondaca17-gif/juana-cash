from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from ..database import get_db
from ..models.venta import Venta, ItemVenta, Pago
from ..models.producto import Producto

router = APIRouter(prefix="/ventas", tags=["Ventas"])

class ItemVentaSchema(BaseModel):
    producto_id: int
    cantidad: float
    precio_unitario: float
    descuento: float = 0

class PagoSchema(BaseModel):
    metodo: str
    monto: float

class VentaCrear(BaseModel):
    usuario_id: int
    cliente_id: Optional[int] = None
    items: List[ItemVentaSchema]
    pagos: List[PagoSchema]
    descuento: float = 0

@router.post("/")
def crear_venta(datos: VentaCrear, db: Session = Depends(get_db)):
    subtotal = sum(i.cantidad * i.precio_unitario - i.descuento for i in datos.items)
    total = subtotal - datos.descuento

    ultima = db.query(Venta).order_by(Venta.id.desc()).first()
    ultimo_num = int(ultima.numero) if ultima and ultima.numero.isdigit() else 0
    numero = f"{ultimo_num + 1:04d}"

    venta = Venta(
        numero=numero,
        usuario_id=datos.usuario_id,
        cliente_id=datos.cliente_id,
        subtotal=subtotal,
        descuento=datos.descuento,
        total=total
    )
    db.add(venta)
    db.flush()

    for item in datos.items:
        iv = ItemVenta(
            venta_id=venta.id,
            producto_id=item.producto_id,
            cantidad=item.cantidad,
            precio_unitario=item.precio_unitario,
            descuento=item.descuento,
            subtotal=item.cantidad * item.precio_unitario - item.descuento
        )
        db.add(iv)
        p = db.query(Producto).filter(Producto.id == item.producto_id).first()
        if p:
            p.stock_actual = float(p.stock_actual) - item.cantidad

    for pago in datos.pagos:
        pg = Pago(venta_id=venta.id, metodo=pago.metodo, monto=pago.monto)
        db.add(pg)

    db.commit()
    db.refresh(venta)
    return {"mensaje": "Venta registrada", "numero": venta.numero, "total": float(venta.total)}

@router.get("/")
def listar_ventas(db: Session = Depends(get_db)):
    return db.query(Venta).order_by(Venta.fecha.desc()).limit(50).all()

@router.get("/{id}")
def obtener_venta(id: int, db: Session = Depends(get_db)):
    v = db.query(Venta).filter(Venta.id == id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    return v