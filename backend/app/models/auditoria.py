from sqlalchemy import Column, Integer, String, DateTime, Float
from datetime import datetime
from ..database import Base

class RegistroBorrados(Base):
    __tablename__ = "registro_borrados"
    
    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(DateTime, default=datetime.now)
    usuario = Column(String) # Quién lo borró (ej: "Fernanda")
    detalle = Column(String) # "Borró 2x Jugo Clight de la venta #400"
    monto_perdido = Column(Float) # El total de lo que se borró