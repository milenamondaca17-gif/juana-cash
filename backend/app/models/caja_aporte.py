from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from datetime import datetime
from ..database import Base

class CajaAporte(Base):
    __tablename__ = "caja_aportes"

    id        = Column(Integer, primary_key=True, index=True)
    turno_id  = Column(Integer, ForeignKey("caja_turnos.id"), nullable=False)
    monto     = Column(Float, nullable=False)
    descripcion = Column(String, default="Aporte de caja")
    fecha     = Column(DateTime, default=datetime.now)
