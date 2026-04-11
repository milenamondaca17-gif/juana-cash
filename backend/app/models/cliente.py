from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base

class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    telefono = Column(String, nullable=True)
    email = Column(String, nullable=True)
    direccion = Column(String, nullable=True)
    fecha_nacimiento = Column(String, nullable=True)
    puntos = Column(Float, default=0)
    limite_credito = Column(Float, default=0)
    deuda_actual = Column(Float, default=0)
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.now)
    notas = Column(String, nullable=True)

    fiados = relationship("Fiado", back_populates="cliente")