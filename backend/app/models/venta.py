from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base

class Venta(Base):
    __tablename__ = "ventas"
    id          = Column(Integer, primary_key=True, index=True)
    numero      = Column(String(20), unique=True, nullable=False)
    usuario_id  = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    cliente_id  = Column(Integer, ForeignKey("clientes.id"), nullable=True)
    fecha       = Column(DateTime, server_default=func.now())
    subtotal    = Column(Numeric(12,2), nullable=False)
    descuento   = Column(Numeric(12,2), default=0)
    recargo     = Column(Numeric(12,2), default=0)
    total       = Column(Numeric(12,2), nullable=False)
    estado      = Column(String(15), default="completada")
    origen      = Column(String(20), default="mostrador")
    
    items       = relationship("ItemVenta", back_populates="venta")
    pagos       = relationship("Pago", back_populates="venta")
    usuario     = relationship("Usuario", foreign_keys=[usuario_id])

class ItemVenta(Base):
    __tablename__ = "items_venta"
    id              = Column(Integer, primary_key=True, index=True)
    venta_id        = Column(Integer, ForeignKey("ventas.id"), nullable=False)
    producto_id     = Column(Integer, ForeignKey("productos.id"), nullable=False)
    cantidad        = Column(Numeric(12,3), nullable=False)
    precio_unitario = Column(Numeric(12,2), nullable=False)
    descuento       = Column(Numeric(12,2), default=0)
    subtotal        = Column(Numeric(12,2), nullable=False)
    venta           = relationship("Venta", back_populates="items")
    producto        = relationship("Producto", back_populates="items_venta")

class Pago(Base):
    __tablename__ = "pagos"
    id       = Column(Integer, primary_key=True, index=True)
    venta_id = Column(Integer, ForeignKey("ventas.id"), nullable=False)
    metodo   = Column(String(20), nullable=False)
    monto    = Column(Numeric(12,2), nullable=False)
    fecha    = Column(DateTime, server_default=func.now())
    venta    = relationship("Venta", back_populates="pagos")