from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from ..database import get_db
from ..models.cliente import Cliente

router = APIRouter(prefix="/clientes", tags=["Clientes"])

class ClienteCrear(BaseModel):
    nombre: str
    dni: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    direccion: Optional[str] = None
    limite_credito: float = 0

@router.get("/")
def listar_clientes(db: Session = Depends(get_db)):
    return db.query(Cliente).filter(Cliente.activo == True).all()

@router.get("/buscar")
def buscar_cliente(q: str, db: Session = Depends(get_db)):
    return db.query(Cliente).filter(
        (Cliente.nombre.contains(q)) | (Cliente.dni == q) | (Cliente.telefono == q),
        Cliente.activo == True
    ).all()

@router.get("/{id}")
def obtener_cliente(id: int, db: Session = Depends(get_db)):
    c = db.query(Cliente).filter(Cliente.id == id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return c

@router.post("/")
def crear_cliente(datos: ClienteCrear, db: Session = Depends(get_db)):
    c = Cliente(**datos.dict())
    db.add(c)
    db.commit()
    db.refresh(c)
    return c

@router.put("/{id}")
def actualizar_cliente(id: int, datos: ClienteCrear, db: Session = Depends(get_db)):
    c = db.query(Cliente).filter(Cliente.id == id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    for key, value in datos.dict().items():
        setattr(c, key, value)
    db.commit()
    db.refresh(c)
    return c