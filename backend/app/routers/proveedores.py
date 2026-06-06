from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
from ..database import get_db
from ..models.proveedor import Proveedor, CompraProveedor, PagoProveedor
from ..models.producto import Producto

router = APIRouter(prefix="/proveedores", tags=["proveedores"])

# ── Schemas ──────────────────────────────────────────────────────────────────

class ProveedorSchema(BaseModel):
    nombre: str
    telefono: Optional[str] = None
    vendedor: Optional[str] = None
    cuit: Optional[str] = None
    dia_visita: Optional[str] = None
    condicion_pago: Optional[str] = "contado"
    notas: Optional[str] = None

class CompraSchema(BaseModel):
    nro_factura: Optional[str] = None
    monto_total: float
    condicion: Optional[str] = "contado"
    fecha_vencimiento: Optional[str] = None
    notas: Optional[str] = None

class PagoSchema(BaseModel):
    compra_id: Optional[int] = None
    monto: float
    metodo_pago: str = "efectivo"
    referencia: Optional[str] = None
    notas: Optional[str] = None

# ── Helpers ───────────────────────────────────────────────────────────────────

def _saldo(proveedor_id: int, db: Session) -> float:
    total_compras = db.query(func.sum(CompraProveedor.monto_total)).filter(
        CompraProveedor.proveedor_id == proveedor_id,
        CompraProveedor.condicion == "credito",
        CompraProveedor.pagado == False
    ).scalar() or 0

    total_pagos = db.query(func.sum(PagoProveedor.monto)).filter(
        PagoProveedor.proveedor_id == proveedor_id
    ).scalar() or 0

    # Saldo = lo que compramos a crédito - lo que ya pagamos
    deuda_credito = float(total_compras)
    pagado = float(total_pagos)

    # También contar compras contado que no tienen pago asociado como "ya pagadas"
    return max(0, deuda_credito - pagado)

def _serializar(p: Proveedor, db: Session) -> dict:
    return {
        "id": p.id,
        "nombre": p.nombre,
        "telefono": p.telefono,
        "vendedor": p.vendedor,
        "cuit": p.cuit,
        "dia_visita": p.dia_visita,
        "condicion_pago": p.condicion_pago,
        "notas": p.notas,
        "saldo_pendiente": _saldo(p.id, db),
        "cantidad_productos": db.query(Producto).filter(
            Producto.proveedor_id == p.id, Producto.activo == True
        ).count(),
    }

# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/")
def listar(db: Session = Depends(get_db)):
    proveedores = db.query(Proveedor).filter(Proveedor.activo == True).order_by(Proveedor.nombre).all()
    return [_serializar(p, db) for p in proveedores]

@router.post("/")
def crear(datos: ProveedorSchema, db: Session = Depends(get_db)):
    p = Proveedor(**datos.model_dump())
    db.add(p); db.commit(); db.refresh(p)
    return _serializar(p, db)

@router.put("/{pid}")
def actualizar(pid: int, datos: ProveedorSchema, db: Session = Depends(get_db)):
    p = db.query(Proveedor).filter(Proveedor.id == pid).first()
    if not p:
        raise HTTPException(404, "Proveedor no encontrado")
    for k, v in datos.model_dump().items():
        setattr(p, k, v)
    db.commit(); db.refresh(p)
    return _serializar(p, db)

@router.delete("/{pid}")
def eliminar(pid: int, db: Session = Depends(get_db)):
    p = db.query(Proveedor).filter(Proveedor.id == pid).first()
    if not p:
        raise HTTPException(404, "Proveedor no encontrado")
    p.activo = False
    db.commit()
    return {"ok": True}

@router.get("/{pid}")
def detalle(pid: int, db: Session = Depends(get_db)):
    p = db.query(Proveedor).filter(Proveedor.id == pid).first()
    if not p:
        raise HTTPException(404, "Proveedor no encontrado")
    return _serializar(p, db)

@router.get("/{pid}/productos")
def productos(pid: int, db: Session = Depends(get_db)):
    prods = db.query(Producto).filter(
        Producto.proveedor_id == pid, Producto.activo == True
    ).order_by(Producto.nombre).all()
    return [{"id": p.id, "nombre": p.nombre, "precio_venta": float(p.precio_venta),
             "precio_costo": float(p.precio_costo or 0), "stock_actual": float(p.stock_actual or 0)} for p in prods]

@router.get("/{pid}/compras")
def compras(pid: int, db: Session = Depends(get_db)):
    cs = db.query(CompraProveedor).filter(
        CompraProveedor.proveedor_id == pid
    ).order_by(CompraProveedor.fecha.desc()).all()
    return [{
        "id": c.id, "fecha": str(c.fecha)[:16], "nro_factura": c.nro_factura,
        "monto_total": float(c.monto_total), "condicion": c.condicion,
        "pagado": c.pagado,
        "fecha_vencimiento": str(c.fecha_vencimiento)[:10] if c.fecha_vencimiento else None,
        "notas": c.notas,
    } for c in cs]

@router.post("/{pid}/compras")
def registrar_compra(pid: int, datos: CompraSchema, db: Session = Depends(get_db)):
    p = db.query(Proveedor).filter(Proveedor.id == pid).first()
    if not p:
        raise HTTPException(404, "Proveedor no encontrado")
    venc = None
    if datos.fecha_vencimiento:
        try:
            venc = datetime.fromisoformat(datos.fecha_vencimiento)
        except Exception:
            pass
    c = CompraProveedor(
        proveedor_id=pid,
        nro_factura=datos.nro_factura,
        monto_total=datos.monto_total,
        condicion=datos.condicion,
        pagado=(datos.condicion == "contado"),
        fecha_vencimiento=venc,
        notas=datos.notas,
    )
    db.add(c); db.commit(); db.refresh(c)
    return {"id": c.id, "ok": True}

@router.get("/{pid}/pagos")
def pagos(pid: int, db: Session = Depends(get_db)):
    ps = db.query(PagoProveedor).filter(
        PagoProveedor.proveedor_id == pid
    ).order_by(PagoProveedor.fecha.desc()).all()
    return [{
        "id": pg.id, "fecha": str(pg.fecha)[:16], "monto": float(pg.monto),
        "metodo_pago": pg.metodo_pago, "referencia": pg.referencia,
        "compra_id": pg.compra_id, "notas": pg.notas,
    } for pg in ps]

@router.post("/{pid}/pagos")
def registrar_pago(pid: int, datos: PagoSchema, db: Session = Depends(get_db)):
    p = db.query(Proveedor).filter(Proveedor.id == pid).first()
    if not p:
        raise HTTPException(404, "Proveedor no encontrado")
    pg = PagoProveedor(
        proveedor_id=pid,
        compra_id=datos.compra_id,
        monto=datos.monto,
        metodo_pago=datos.metodo_pago,
        referencia=datos.referencia,
        notas=datos.notas,
    )
    db.add(pg)
    if datos.compra_id:
        compra = db.query(CompraProveedor).filter(CompraProveedor.id == datos.compra_id).first()
        if compra:
            compra.pagado = True
    db.commit(); db.refresh(pg)
    return {"id": pg.id, "ok": True}

@router.get("/{pid}/saldo")
def saldo(pid: int, db: Session = Depends(get_db)):
    return {"saldo": _saldo(pid, db)}
