from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, datetime
from ..database import get_db
from ..models.gasto import Gasto
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/gastos", tags=["Gastos"])

class GastoCreate(BaseModel):
    descripcion: str
    monto: float
    categoria: Optional[str] = "general"
    usuario_id: Optional[int] = 1

@router.post("/")
def crear_gasto(gasto: GastoCreate, db: Session = Depends(get_db)):
    if gasto.monto <= 0:
        raise HTTPException(status_code=400, detail="El monto debe ser mayor a cero")
    nuevo = Gasto(
        descripcion=gasto.descripcion,
        monto=gasto.monto,
        categoria=gasto.categoria,
        usuario_id=gasto.usuario_id
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return {"id": nuevo.id, "descripcion": nuevo.descripcion, "monto": nuevo.monto}

@router.get("/hoy")
def gastos_hoy(desde: Optional[str] = None, db: Session = Depends(get_db)):
    if desde:
        try:
            dt_desde = datetime.fromisoformat(desde.replace("T", " "))
            gastos = db.query(Gasto).filter(
                Gasto.fecha >= dt_desde
            ).order_by(Gasto.fecha.desc()).all()
        except Exception:
            hoy = date.today()
            gastos = db.query(Gasto).filter(
                func.date(Gasto.fecha) == hoy
            ).order_by(Gasto.fecha.desc()).all()
    else:
        hoy = date.today()
        gastos = db.query(Gasto).filter(
            func.date(Gasto.fecha) == hoy
        ).order_by(Gasto.fecha.desc()).all()
    total = sum(g.monto for g in gastos)
    return {
        "gastos": [
            {
                "id": g.id,
                "descripcion": g.descripcion,
                "monto": g.monto,
                "categoria": g.categoria,
                "hora": g.fecha.strftime("%H:%M")
            }
            for g in gastos
        ],
        "total": total
    }

@router.get("/mes")
def gastos_mes(db: Session = Depends(get_db)):
    hoy = date.today()
    desde = hoy.replace(day=1)
    gastos = db.query(Gasto).filter(
        func.date(Gasto.fecha) >= desde
    ).order_by(Gasto.fecha.desc()).all()
    total = sum(g.monto for g in gastos)
    por_categoria = {}
    for g in gastos:
        por_categoria[g.categoria] = por_categoria.get(g.categoria, 0) + g.monto
    return {
        "gastos": [
            {
                "id": g.id,
                "descripcion": g.descripcion,
                "monto": g.monto,
                "categoria": g.categoria,
                "fecha": g.fecha.strftime("%d/%m %H:%M")
            }
            for g in gastos
        ],
        "total": total,
        "por_categoria": por_categoria
    }

@router.delete("/{gasto_id}")
def eliminar_gasto(gasto_id: int, db: Session = Depends(get_db)):
    gasto = db.query(Gasto).filter(Gasto.id == gasto_id).first()
    if gasto:
        db.delete(gasto)
        db.commit()
    return {"ok": True}