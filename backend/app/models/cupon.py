from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class Cupon(Base):
    __tablename__ = "cupones"

    id          = Column(Integer, primary_key=True, index=True)
    codigo      = Column(String(20), unique=True, nullable=False, index=True)
    porcentaje  = Column(Float, nullable=False)           # 10 = 10%
    cliente_id  = Column(Integer, ForeignKey("clientes.id"), nullable=True)
    usado       = Column(Boolean, default=False)
    creado_en   = Column(DateTime, server_default=func.now())
    usado_en    = Column(DateTime, nullable=True)
    venta_id    = Column(Integer, nullable=True)          # qué venta lo usó
    creado_por  = Column(String(100), default="sistema")  # usuario que lo generó

    cliente = relationship("Cliente")
