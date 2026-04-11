from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base

class Categoria(Base):
    __tablename__ = "categorias"
    id        = Column(Integer, primary_key=True, index=True)
    nombre    = Column(String(100), nullable=False)
    padre_id  = Column(Integer, ForeignKey("categorias.id"), nullable=True)
    activo    = Column(Boolean, default=True)
    productos = relationship("Producto", back_populates="categoria")

class Producto(Base):
    __tablename__ = "productos"
    id           = Column(Integer, primary_key=True, index=True)
    codigo_barra = Column(String(50), unique=True, nullable=True)
    nombre       = Column(String(200), nullable=False)
    descripcion  = Column(String(500), nullable=True)
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=True)
    precio_venta = Column(Numeric(12,2), nullable=False)
    precio_costo = Column(Numeric(12,2), nullable=True)
    tasa_iva     = Column(Numeric(5,2), default=21.00)
    stock_actual = Column(Numeric(12,3), default=0)
    stock_minimo = Column(Numeric(12,3), default=0)
    pesable      = Column(Boolean, default=False)
    activo       = Column(Boolean, default=True)
    created_at   = Column(DateTime, server_default=func.now())
    updated_at   = Column(DateTime, server_default=func.now(), onupdate=func.now())
    categoria    = relationship("Categoria", back_populates="productos")
    items_venta  = relationship("ItemVenta", back_populates="producto")