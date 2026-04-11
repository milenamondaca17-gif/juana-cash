from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from datetime import datetime
from ..database import Base

class Gasto(Base):
    __tablename__ = "gastos"

    id = Column(Integer, primary_key=True, index=True)
    descripcion = Column(String, nullable=False)
    monto = Column(Float, nullable=False)
    categoria = Column(String, default="general")
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    fecha = Column(DateTime, default=datetime.now)