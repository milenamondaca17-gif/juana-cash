from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base

class Categoria(Base):
    __tablename__ = "categorias"
    id        = Column(Integer, primary_key=True, index=True)
    nombre    = Column(String(100), nullable=False)
    padre_id  = Column(Integer, ForeignKey("categorias.id"), nullable=True)
    activo    = Column(Boolean, default=True)
    
    productos = relationship("Producto", back_populates="categoria")

class CodigoBarra(Base):
    """Nueva tabla para soportar múltiples códigos para un mismo producto (ej: Clight)"""
    __tablename__ = "codigos_barra"
    id          = Column(Integer, primary_key=True, index=True)
    codigo      = Column(String(50), unique=True, nullable=False, index=True)
    producto_id = Column(Integer, ForeignKey("productos.id"))
    
    producto    = relationship("Producto", back_populates="codigos_extra")

class Producto(Base):
    __tablename__ = "productos"
    id           = Column(Integer, primary_key=True, index=True)
    codigo_barra = Column(String(50), unique=True, nullable=True) # Código principal
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
    created_at   = Column(DateTime, default=datetime.now)
    updated_at   = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    proveedor_id  = Column(Integer, ForeignKey("proveedores.id"), nullable=True)

    # Relaciones
    categoria     = relationship("Categoria", back_populates="productos")
    items_venta   = relationship("ItemVenta", back_populates="producto")
    codigos_extra = relationship("CodigoBarra", back_populates="producto", cascade="all, delete-orphan")
    proveedor     = relationship("Proveedor", back_populates="productos")