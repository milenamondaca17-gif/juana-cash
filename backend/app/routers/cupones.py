from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from ..database import get_db
from ..models.cupon import Cupon
from ..models.cliente import Cliente

router = APIRouter(prefix="/cupones", tags=["Cupones"])

PIN_DUENO = "1722"

class GenerarCuponSchema(BaseModel):
    cliente_id: int
    porcentaje: float
    pin_dueno:  str

class UsarCuponSchema(BaseModel):
    venta_id: int = None


def _generar_codigo_unico(db: Session) -> str:
    import random, string
    while True:
        codigo = "DESC" + "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
        existente = db.query(Cupon).filter(Cupon.codigo == codigo).first()
        if not existente:
            return codigo


@router.post("/generar")
def generar_cupon(datos: GenerarCuponSchema, db: Session = Depends(get_db)):
    if datos.pin_dueno != PIN_DUENO:
        raise HTTPException(status_code=403, detail="PIN de dueño incorrecto")
    if datos.porcentaje <= 0 or datos.porcentaje > 100:
        raise HTTPException(status_code=400, detail="Porcentaje inválido (1-100)")

    cliente = db.query(Cliente).filter(Cliente.id == datos.cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    # Un cliente solo puede tener 1 cupón activo a la vez
    cupon_activo = db.query(Cupon).filter(
        Cupon.cliente_id == datos.cliente_id,
        Cupon.usado == False
    ).first()
    if cupon_activo:
        raise HTTPException(
            status_code=409,
            detail=f"El cliente ya tiene un cupón activo: {cupon_activo.codigo} ({cupon_activo.porcentaje:.0f}%). Usalo o eliminalo antes de generar uno nuevo."
        )

    codigo = _generar_codigo_unico(db)
    cupon = Cupon(
        codigo=codigo,
        porcentaje=datos.porcentaje,
        cliente_id=datos.cliente_id,
    )
    db.add(cupon)
    db.commit()
    db.refresh(cupon)

    return {
        "codigo":      cupon.codigo,
        "porcentaje":  cupon.porcentaje,
        "cliente_id":  cupon.cliente_id,
        "cliente":     cliente.nombre,
        "creado_en":   str(cupon.creado_en),
    }


@router.get("/validar/{codigo}")
def validar_cupon(codigo: str, db: Session = Depends(get_db)):
    cupon = db.query(Cupon).filter(Cupon.codigo == codigo.upper()).first()
    if not cupon:
        return {"valido": False, "motivo": "Código no existe"}
    if cupon.usado:
        usado_en = str(cupon.usado_en)[:16] if cupon.usado_en else "?"
        return {"valido": False, "motivo": f"Cupón ya utilizado el {usado_en}"}

    cliente_nombre = cupon.cliente.nombre if cupon.cliente else "Sin cliente"
    return {
        "valido":      True,
        "codigo":      cupon.codigo,
        "porcentaje":  cupon.porcentaje,
        "cliente_id":  cupon.cliente_id,
        "cliente":     cliente_nombre,
        "creado_en":   str(cupon.creado_en)[:16],
    }


@router.post("/usar/{codigo}")
def usar_cupon(codigo: str, datos: UsarCuponSchema = None, db: Session = Depends(get_db)):
    cupon = db.query(Cupon).filter(Cupon.codigo == codigo.upper()).first()
    if not cupon:
        raise HTTPException(status_code=404, detail="Cupón no encontrado")
    if cupon.usado:
        raise HTTPException(status_code=409, detail="Cupón ya fue utilizado")

    cupon.usado    = True
    cupon.usado_en = datetime.now()
    if datos and datos.venta_id:
        cupon.venta_id = datos.venta_id
    db.commit()
    return {"ok": True, "codigo": cupon.codigo, "porcentaje": cupon.porcentaje}


@router.delete("/eliminar/{codigo}")
def eliminar_cupon(codigo: str, pin: str, db: Session = Depends(get_db)):
    if pin != PIN_DUENO:
        raise HTTPException(status_code=403, detail="PIN incorrecto")
    cupon = db.query(Cupon).filter(Cupon.codigo == codigo.upper()).first()
    if not cupon:
        raise HTTPException(status_code=404, detail="Cupón no encontrado")
    if cupon.usado:
        raise HTTPException(status_code=409, detail="No se puede eliminar un cupón ya usado")
    db.delete(cupon)
    db.commit()
    return {"ok": True}


@router.get("/cliente/{cliente_id}")
def cupones_cliente(cliente_id: int, db: Session = Depends(get_db)):
    cupones = db.query(Cupon).filter(Cupon.cliente_id == cliente_id).order_by(Cupon.creado_en.desc()).all()
    return [{
        "codigo":     c.codigo,
        "porcentaje": c.porcentaje,
        "usado":      c.usado,
        "creado_en":  str(c.creado_en)[:16],
        "usado_en":   str(c.usado_en)[:16] if c.usado_en else None,
    } for c in cupones]


@router.get("/todos")
def listar_cupones(db: Session = Depends(get_db)):
    cupones = db.query(Cupon).order_by(Cupon.creado_en.desc()).limit(200).all()
    return [{
        "id":         c.id,
        "codigo":     c.codigo,
        "porcentaje": c.porcentaje,
        "usado":      c.usado,
        "cliente":    c.cliente.nombre if c.cliente else "-",
        "creado_en":  str(c.creado_en)[:16],
        "usado_en":   str(c.usado_en)[:16] if c.usado_en else None,
    } for c in cupones]
