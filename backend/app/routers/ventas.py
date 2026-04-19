from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from ..database import get_db
from ..models.venta import Venta, ItemVenta, Pago
from ..models.producto import Producto
from ..models.usuario import Usuario
from ..models.cliente import Cliente
from ..models.fiado import Fiado
from passlib.context import CryptContext

router = APIRouter(prefix="/ventas", tags=["Ventas"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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
    origen: str = "mostrador"  # mostrador | celular | delivery

class AnularVentaSchema(BaseModel):
    motivo: str
    password_admin: str
    usuario_id: int

@router.post("/")
def crear_venta(datos: VentaCrear, db: Session = Depends(get_db)):
    subtotal = sum(i.cantidad * i.precio_unitario - i.descuento for i in datos.items)
    total = subtotal - datos.descuento

    # Número de venta único
    ultima = db.query(Venta).order_by(Venta.id.desc()).first()
    ultimo_num = int(ultima.numero) if ultima and ultima.numero.isdigit() else 0
    numero = f"{ultimo_num + 1:04d}"

    venta = Venta(
        numero=numero,
        usuario_id=datos.usuario_id,
        cliente_id=datos.cliente_id,
        subtotal=subtotal,
        descuento=datos.descuento,
        total=total,
        origen=datos.origen,
        fecha=datetime.now()  # Hora local, no UTC
    )
    db.add(venta)
    db.flush()

    # Registrar items y descontar stock
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
            stock_nuevo = float(p.stock_actual) - item.cantidad
            if stock_nuevo < 0:
                stock_nuevo = 0
            p.stock_actual = stock_nuevo

    # Registrar pagos — CORREGIDO: el bloque de fiado va DENTRO del for
    for pago in datos.pagos:
        pg = Pago(venta_id=venta.id, metodo=pago.metodo, monto=pago.monto)
        db.add(pg)

        # Si el método es fiado, registrar la deuda al cliente
        if pago.metodo.lower() == "fiado" and datos.cliente_id:
            cliente = db.query(Cliente).filter(Cliente.id == datos.cliente_id).first()
            if cliente:
                # Actualizar deuda_actual (campo correcto del modelo)
                cliente.deuda_actual = float(cliente.deuda_actual or 0) + float(pago.monto)

                # Crear registro en tabla fiados
                fiado = Fiado(
                    cliente_id=datos.cliente_id,
                    venta_id=venta.id,
                    monto=pago.monto,
                    saldo=pago.monto,
                    estado="pendiente"
                )
                db.add(fiado)

    db.commit()
    db.refresh(venta)
    return {
        "mensaje": "Venta registrada",
        "numero": venta.numero,
        "total": float(venta.total)
    }

@router.get("/")
def listar_ventas(db: Session = Depends(get_db)):
    ventas = db.query(Venta).order_by(Venta.fecha.desc()).limit(50).all()
    resultado = []
    for v in ventas:
        metodo = v.pagos[0].metodo if v.pagos else "efectivo"
        resultado.append({
            "id": v.id,
            "numero": v.numero,
            "total": float(v.total),
            "estado": v.estado,
            "metodo_pago": metodo,
            "fecha": str(v.fecha)
        })
    return resultado

@router.get("/{id}")
def obtener_venta(id: int, db: Session = Depends(get_db)):
    v = db.query(Venta).filter(Venta.id == id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    return v

@router.post("/{id}/anular")
def anular_venta(id: int, datos: AnularVentaSchema, db: Session = Depends(get_db)):
    venta = db.query(Venta).filter(Venta.id == id).first()
    if not venta:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    if venta.estado == "anulada":
        raise HTTPException(status_code=400, detail="La venta ya está anulada")

    # Verificar contraseña del admin
    usuario = db.query(Usuario).filter(
        Usuario.id == datos.usuario_id,
        Usuario.rol.in_(["admin", "encargado"]),
        Usuario.activo == True
    ).first()
    if not usuario:
        raise HTTPException(status_code=403, detail="Usuario no tiene permisos para anular")
    if not pwd_context.verify(datos.password_admin, usuario.password_hash):
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")

    # Devolver stock
    for item in venta.items:
        producto = db.query(Producto).filter(Producto.id == item.producto_id).first()
        if producto:
            producto.stock_actual = float(producto.stock_actual) + float(item.cantidad)

    # Revertir deuda del cliente si había fiado
    for pago in venta.pagos:
        if pago.metodo.lower() == "fiado" and venta.cliente_id:
            cliente = db.query(Cliente).filter(Cliente.id == venta.cliente_id).first()
            if cliente:
                cliente.deuda_actual = max(0, float(cliente.deuda_actual or 0) - float(pago.monto))
            # Marcar el fiado como anulado
            fiado = db.query(Fiado).filter(
                Fiado.venta_id == venta.id,
                Fiado.cliente_id == venta.cliente_id
            ).first()
            if fiado:
                fiado.estado = "anulado"
                fiado.saldo = 0

    # Revertir puntos del cliente si los tiene
    if venta.cliente_id:
        cliente = db.query(Cliente).filter(Cliente.id == venta.cliente_id).first()
        if cliente:
            puntos_a_quitar = int(float(venta.total) // 100)
            if puntos_a_quitar > 0:
                cliente.puntos = max(0, float(cliente.puntos or 0) - puntos_a_quitar)

    venta.estado = "anulada"
    db.commit()

    return {
        "mensaje": f"Venta {venta.numero} anulada correctamente",
        "motivo": datos.motivo
    }
