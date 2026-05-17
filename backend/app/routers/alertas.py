from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.alerta_precio import AlertaPrecio

router = APIRouter(prefix="/alertas-precio", tags=["Alertas"])

@router.get("/")
def listar_alertas(solo_no_vistas: bool = False, db: Session = Depends(get_db)):
    q = db.query(AlertaPrecio)
    if solo_no_vistas:
        q = q.filter(AlertaPrecio.visto == False)
    alertas = q.order_by(AlertaPrecio.creado_en.desc()).limit(100).all()
    return [{
        "id":              a.id,
        "producto_id":     a.producto_id,
        "nombre_producto": a.nombre_producto,
        "precio_anterior": float(a.precio_anterior),
        "precio_nuevo":    float(a.precio_nuevo),
        "usuario":         a.usuario,
        "visto":           a.visto,
        "creado_en":       str(a.creado_en),
    } for a in alertas]

@router.get("/pendientes")
def contar_pendientes(db: Session = Depends(get_db)):
    n = db.query(AlertaPrecio).filter(AlertaPrecio.visto == False).count()
    return {"pendientes": n}

@router.post("/{id}/visto")
def marcar_visto(id: int, db: Session = Depends(get_db)):
    a = db.query(AlertaPrecio).filter(AlertaPrecio.id == id).first()
    if a:
        a.visto = True
        db.commit()
    return {"ok": True}

@router.post("/marcar-todas-vistas")
def marcar_todas_vistas(db: Session = Depends(get_db)):
    db.query(AlertaPrecio).filter(AlertaPrecio.visto == False).update({"visto": True}, synchronize_session=False)
    db.commit()
    return {"ok": True}
