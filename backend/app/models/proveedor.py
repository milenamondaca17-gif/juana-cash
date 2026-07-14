from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base

class Proveedor(Base):
    __tablename__ = "proveedores"
    id              = Column(Integer, primary_key=True, index=True)
    nombre          = Column(String(200), nullable=False)
    telefono        = Column(String(50))
    vendedor        = Column(String(200))
    cuit            = Column(String(20))
    dia_visita      = Column(String(20))   # Lunes, Martes, etc.
    condicion_pago  = Column(String(20), default="contado")  # contado, 7dias, 15dias, 30dias
    notas           = Column(String(500))
    activo          = Column(Boolean, default=True)
    created_at      = Column(DateTime, default=datetime.now)

    productos       = relationship("Producto", back_populates="proveedor")
    compras         = relationship("CompraProveedor", back_populates="proveedor", cascade="all, delete-orphan")
    pagos           = relationship("PagoProveedor", back_populates="proveedor", cascade="all, delete-orphan")


class CompraProveedor(Base):
    __tablename__ = "compras_proveedor"
    id                  = Column(Integer, primary_key=True, index=True)
    proveedor_id        = Column(Integer, ForeignKey("proveedores.id"), nullable=False)
    fecha               = Column(DateTime, default=datetime.now)
    nro_factura         = Column(String(50))
    monto_total         = Column(Numeric(12, 2), default=0)
    condicion           = Column(String(20), default="contado")  # contado, credito
    pagado              = Column(Boolean, default=False)
    fecha_vencimiento   = Column(DateTime, nullable=True)
    notas               = Column(String(500))

    proveedor           = relationship("Proveedor", back_populates="compras")
    pagos               = relationship("PagoProveedor", back_populates="compra")
    items               = relationship("ItemCompraProveedor", back_populates="compra", cascade="all, delete-orphan")


class ItemCompraProveedor(Base):
    __tablename__ = "items_compra_proveedor"
    id              = Column(Integer, primary_key=True, index=True)
    compra_id       = Column(Integer, ForeignKey("compras_proveedor.id"), nullable=False)
    producto_id     = Column(Integer, ForeignKey("productos.id"), nullable=True)
    descripcion     = Column(String(200))   # nombre libre si no hay producto en sistema
    cantidad        = Column(Numeric(12, 3), default=1)
    precio_unitario = Column(Numeric(12, 2), default=0)
    subtotal        = Column(Numeric(12, 2), default=0)

    compra          = relationship("CompraProveedor", back_populates="items")


class PagoProveedor(Base):
    __tablename__ = "pagos_proveedor"
    id              = Column(Integer, primary_key=True, index=True)
    proveedor_id    = Column(Integer, ForeignKey("proveedores.id"), nullable=False)
    compra_id       = Column(Integer, ForeignKey("compras_proveedor.id"), nullable=True)
    fecha           = Column(DateTime, default=datetime.now)
    monto           = Column(Numeric(12, 2), default=0)
    metodo_pago     = Column(String(30), default="efectivo")  # efectivo, transferencia, cheque, debito
    referencia      = Column(String(200))   # nro de transferencia, cheque, etc.
    notas           = Column(String(500))

    proveedor       = relationship("Proveedor", back_populates="pagos")
    compra          = relationship("CompraProveedor", back_populates="pagos")
