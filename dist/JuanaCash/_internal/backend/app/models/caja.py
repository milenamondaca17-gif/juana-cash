from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.app.database import Base

class Caja(Base):
    __tablename__ = "caja"
    
    id = Column(Integer, primary_key=True, index=True)
    sesion_id = Column(Integer, ForeignKey("sesiones.id"), nullable=False)
    tipo = Column(String, nullable=False)  # ingreso, egreso
    concepto = Column(String, nullable=False)
    monto = Column(Float, nullable=False)
    metodo = Column(String, nullable=False)  # efectivo, tarjeta, transferencia
    descripcion = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    sesion = relationship("Sesion")