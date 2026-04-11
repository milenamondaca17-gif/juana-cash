from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from ..database import get_db
from ..models.producto import Producto, Categoria

router = APIRouter(prefix="/productos", tags=["Productos"])

class ProductoCrear(BaseModel):
    codigo_barra: Optional[str] = None
    nombre: str
    precio_venta: float
    precio_costo: Optional[float] = None
    stock_actual: float = 0
    stock_minimo: float = 0
    categoria_id: Optional[int] = None
    tasa_iva: float = 21.0

@router.get("/")
def listar_productos(db: Session = Depends(get_db)):
    return db.query(Producto).filter(Producto.activo == True).all()

@router.get("/buscar")
def buscar_producto(q: str, db: Session = Depends(get_db)):
    return db.query(Producto).filter(
        (Producto.nombre.contains(q)) | (Producto.codigo_barra == q),
        Producto.activo == True
    ).all()

@router.get("/{id}")
def obtener_producto(id: int, db: Session = Depends(get_db)):
    p = db.query(Producto).filter(Producto.id == id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return p

@router.post("/")
def crear_producto(datos: ProductoCrear, db: Session = Depends(get_db)):
    p = Producto(**datos.dict())
    db.add(p)
    db.commit()
    db.refresh(p)
    return p

@router.put("/{id}")
def actualizar_producto(id: int, datos: ProductoCrear, db: Session = Depends(get_db)):
    p = db.query(Producto).filter(Producto.id == id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    for key, value in datos.dict().items():
        setattr(p, key, value)
    db.commit()
    db.refresh(p)
    return p

@router.delete("/{id}")
def eliminar_producto(id: int, db: Session = Depends(get_db)):
    p = db.query(Producto).filter(Producto.id == id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    p.activo = False
    db.commit()
    return {"mensaje": "Producto desactivado"}