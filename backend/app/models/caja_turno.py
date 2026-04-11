from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey
from sqlalchemy.sql import func
from ..database import Base

class CajaTurno(Base):
    __tablename__ = "caja_turnos"
    id                     = Column(Integer, primary_key=True, index=True)
    usuario_id             = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    apertura               = Column(DateTime, server_default=func.now())
    cierre                 = Column(DateTime, nullable=True)
    monto_apertura         = Column(Numeric(12,2), default=0)
    monto_cierre_declarado = Column(Numeric(12,2), nullable=True)
    monto_cierre_calculado = Column(Numeric(12,2), nullable=True)
    diferencia             = Column(Numeric(12,2), nullable=True)
    estado                 = Column(String(10), default="abierto")