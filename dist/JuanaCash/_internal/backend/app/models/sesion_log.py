from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base

class SesionLog(Base):
    __tablename__ = "sesiones_log"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    nombre_cajero = Column(String, nullable=False)
    turno = Column(String, nullable=True)
    accion = Column(String, nullable=False)
    detalle = Column(String, nullable=True)
    fecha = Column(DateTime, default=datetime.now)

    usuario = relationship("Usuario")