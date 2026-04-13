from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.app.database import Base

class Sesion(Base):
    __tablename__ = "sesiones"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    turno = Column(String, nullable=False)  # mañana, tarde, noche
    monto_inicial = Column(Float, default=0.0)
    monto_final = Column(Float, nullable=True)
    activa = Column(Boolean, default=True)
    fecha_apertura = Column(DateTime, default=datetime.utcnow)
    fecha_cierre = Column(DateTime, nullable=True)
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="sesiones")
    ventas = relationship("Venta", back_populates="sesion")
    gastos = relationship("Gasto", back_populates="sesion")