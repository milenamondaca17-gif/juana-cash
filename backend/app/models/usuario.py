from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    pin = Column(String, nullable=True)
    rol = Column(String, default="cajero")
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.now)
    ultimo_acceso = Column(DateTime, nullable=True)

    ventas = relationship("Venta", back_populates="usuario")
    sesiones = relationship("SesionLog", back_populates="sesiones")