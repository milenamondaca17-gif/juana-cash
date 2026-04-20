from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, Date
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base

class Fiado(Base):
    __tablename__ = "fiados"
    id           = Column(Integer, primary_key=True, index=True)
    cliente_id   = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    venta_id     = Column(Integer, ForeignKey("ventas.id"), nullable=True)
    monto        = Column(Numeric(12,2), nullable=False)
    monto_pagado = Column(Numeric(12,2), default=0)
    saldo        = Column(Numeric(12,2), nullable=False)
    estado       = Column(String(15), default="pendiente")
    vencimiento  = Column(Date, nullable=True)
    created_at   = Column(DateTime, server_default=func.now())
    cliente      = relationship("Cliente")

class PagoFiado(Base):
    __tablename__ = "pagos_fiado"
    id          = Column(Integer, primary_key=True, index=True)
    fiado_id    = Column(Integer, ForeignKey("fiados.id"), nullable=False)
    usuario_id  = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    monto       = Column(Numeric(12,2), nullable=False)
    metodo      = Column(String(20), nullable=True)
    observacion = Column(String(300), nullable=True)
    fecha       = Column(DateTime, server_default=func.now())
    fiado       = relationship("Fiado")