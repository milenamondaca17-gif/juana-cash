from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from ..database import get_db
from ..models.fiado import Fiado, PagoFiado
from ..models.cliente import Cliente

router = APIRouter(prefix="/fiados", tags=["Fiados"])

class FiadoCrear(BaseModel):
    cliente_id: int
    venta_id: Optional[int] = None
    monto: float
    saldo: float

class PagoFiadoCrear(BaseModel):
    fiado_id: int
    usuario_id: int
    monto: float
    metodo: str = "efectivo"
    observacion: Optional[str] = None

@router.get("/")
def listar_fiados(db: Session = Depends(get_db)):
    return db.query(Fiado).filter(Fiado.estado != "pagado").all()

@router.get("/cliente/{cliente_id}")
def fiados_cliente(cliente_id: int, db: Session = Depends(get_db)):
    return db.query(Fiado).filter(Fiado.cliente_id == cliente_id).all()

@router.post("/")
def crear_fiado(datos: FiadoCrear, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.id == datos.cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    fiado = Fiado(cliente_id=datos.cliente_id, venta_id=datos.venta_id,
                  monto=datos.monto, saldo=datos.saldo, estado="pendiente")
    db.add(fiado)
    cliente.saldo_deuda = float(cliente.saldo_deuda or 0) + datos.monto
    db.commit()
    db.refresh(fiado)
    return {"mensaje": "Fiado registrado", "id": fiado.id}

@router.post("/pagar")
def pagar_fiado(datos: PagoFiadoCrear, db: Session = Depends(get_db)):
    fiado = db.query(Fiado).filter(Fiado.id == datos.fiado_id).first()
    if not fiado:
        raise HTTPException(status_code=404, detail="Fiado no encontrado")
    fiado.monto_pagado = float(fiado.monto_pagado or 0) + datos.monto
    fiado.saldo = max(0, float(fiado.saldo) - datos.monto)
    fiado.estado = "pagado" if fiado.saldo <= 0 else "parcial"
    cliente = db.query(Cliente).filter(Cliente.id == fiado.cliente_id).first()
    if cliente:
        cliente.saldo_deuda = max(0, float(cliente.saldo_deuda or 0) - datos.monto)
    pago = PagoFiado(fiado_id=datos.fiado_id, usuario_id=datos.usuario_id,
                     monto=datos.monto, metodo=datos.metodo, observacion=datos.observacion)
    db.add(pago)
    db.commit()
    return {"mensaje": "Pago registrado", "saldo_restante": float(fiado.saldo)}