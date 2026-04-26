from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base

class AlertaPrecio(Base):
    __tablename__ = "alertas_precio"
    id              = Column(Integer, primary_key=True, index=True)
    producto_id     = Column(Integer, ForeignKey("productos.id"), nullable=False)
    nombre_producto = Column(String(200), nullable=False)
    precio_anterior = Column(Numeric(12, 2), nullable=False)
    precio_nuevo    = Column(Numeric(12, 2), nullable=False)
    usuario         = Column(String(100), default="mobile")
    visto           = Column(Boolean, default=False)
    creado_en       = Column(DateTime, server_default=func.now())

    producto = relationship("Producto")
