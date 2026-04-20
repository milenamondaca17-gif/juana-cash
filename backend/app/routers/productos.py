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

class ActualizacionMasiva(BaseModel):
    porcentaje: float          # ej: 15.0 = +15%
    redondeo: int = 0          # 0=sin redondeo, 10, 50, 100
    categoria_id: Optional[int] = None  # None = todos
    solo_precio_venta: bool = True

class PreciosDiferenciados(BaseModel):
    producto_id: int
    precio_minorista: float
    precio_mayorista: Optional[float] = None
    precio_vip: Optional[float] = None

@router.get("/")
def listar_productos(db: Session = Depends(get_db)):
    return db.query(Producto).filter(Producto.activo == True).all()

@router.get("/buscar")
def buscar_producto(q: str, db: Session = Depends(get_db)):
    return db.query(Producto).filter(
        (Producto.nombre.contains(q)) | (Producto.codigo_barra == q),
        Producto.activo == True
    ).limit(20).all()

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

# ─── SEMANA 5: Actualización masiva de precios ────────────────────────────────

def aplicar_redondeo(precio: float, redondeo: int) -> float:
    if redondeo <= 0:
        return round(precio, 2)
    import math
    return math.ceil(precio / redondeo) * redondeo

@router.post("/actualizacion-masiva")
def actualizacion_masiva(datos: ActualizacionMasiva, db: Session = Depends(get_db)):
    """Actualiza precios de todos los productos (o una categoría) por un porcentaje."""
    query = db.query(Producto).filter(Producto.activo == True)
    if datos.categoria_id:
        query = query.filter(Producto.categoria_id == datos.categoria_id)
    productos = query.all()

    actualizados = []
    for p in productos:
        precio_anterior = float(p.precio_venta)
        nuevo_precio = precio_anterior * (1 + datos.porcentaje / 100)
        nuevo_precio = aplicar_redondeo(nuevo_precio, datos.redondeo)
        p.precio_venta = nuevo_precio
        if not datos.solo_precio_venta and p.precio_costo:
            p.precio_costo = aplicar_redondeo(
                float(p.precio_costo) * (1 + datos.porcentaje / 100),
                datos.redondeo
            )
        actualizados.append({
            "id": p.id,
            "nombre": p.nombre,
            "precio_anterior": precio_anterior,
            "precio_nuevo": nuevo_precio
        })

    db.commit()
    return {
        "ok": True,
        "actualizados": len(actualizados),
        "porcentaje": datos.porcentaje,
        "redondeo": datos.redondeo,
        "detalle": actualizados
    }

@router.get("/preview-actualizacion")
def preview_actualizacion(
    porcentaje: float,
    redondeo: int = 0,
    categoria_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Vista previa de cómo quedarían los precios antes de aplicar."""
    query = db.query(Producto).filter(Producto.activo == True)
    if categoria_id:
        query = query.filter(Producto.categoria_id == categoria_id)
    productos = query.limit(20).all()

    return [
        {
            "nombre": p.nombre,
            "precio_actual": float(p.precio_venta),
            "precio_nuevo": aplicar_redondeo(
                float(p.precio_venta) * (1 + porcentaje / 100), redondeo
            )
        }
        for p in productos
    ]

@router.get("/categorias")
def listar_categorias(db: Session = Depends(get_db)):
    return db.query(Categoria).filter(Categoria.activo == True).all()
