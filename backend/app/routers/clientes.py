from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import date
from ..database import get_db
from ..models.cliente import Cliente
from ..models.fiado import Fiado, PagoFiado
from ..models.venta import Venta, ItemVenta
from ..models.producto import Producto

router = APIRouter(prefix="/clientes", tags=["Clientes"])

class ClienteCrear(BaseModel):
    nombre: str
    telefono: Optional[str] = None
    email: Optional[str] = None
    direccion: Optional[str] = None
    fecha_nacimiento: Optional[str] = None
    limite_credito: float = 0
    notas: Optional[str] = None

# ─── RUTAS ESPECIALES (deben ir ANTES de /{id}) ───────────────────────────────

@router.get("/cumpleanos")
def cumpleanos(db: Session = Depends(get_db)):
    """Clientes con cumpleaños hoy o en los próximos 7 días."""
    hoy = date.today()
    clientes = db.query(Cliente).filter(
        Cliente.activo == True,
        Cliente.fecha_nacimiento != None
    ).all()
    resultado = []
    for c in clientes:
        try:
            fn = str(c.fecha_nacimiento).strip()
            if not fn or fn == "None":
                continue
            if "/" in fn:
                partes = fn.split("/")
                dia, mes = int(partes[0]), int(partes[1])
            else:
                partes = fn.split("-")
                mes, dia = int(partes[1]), int(partes[2][:2])
            tipo = None
            if mes == hoy.month and dia == hoy.day:
                tipo = "hoy"
            elif mes == hoy.month and 0 < (dia - hoy.day) <= 7:
                tipo = "proximo"
            if tipo:
                resultado.append({
                    "id": c.id,
                    "nombre": c.nombre,
                    "telefono": c.telefono or "",
                    "tipo": tipo,
                    "dia": dia,
                    "mes": mes
                })
        except Exception:
            continue
    return resultado

@router.get("/deudores")
def deudores(db: Session = Depends(get_db)):
    """Clientes con deuda mayor a 0, ordenados por monto."""
    clientes = db.query(Cliente).filter(
        Cliente.activo == True,
        Cliente.deuda_actual > 0
    ).order_by(Cliente.deuda_actual.desc()).all()
    return [
        {
            "id": c.id,
            "nombre": c.nombre,
            "telefono": c.telefono or "",
            "deuda_actual": float(c.deuda_actual),
            "limite_credito": float(c.limite_credito)
        }
        for c in clientes
    ]

@router.get("/buscar")
def buscar_cliente(q: str, db: Session = Depends(get_db)):
    return db.query(Cliente).filter(
        (Cliente.nombre.contains(q)) | (Cliente.telefono == q),
        Cliente.activo == True
    ).all()

@router.get("/")
def listar_clientes(db: Session = Depends(get_db)):
    return db.query(Cliente).filter(Cliente.activo == True).all()

# ─── RUTAS CON /{id} ──────────────────────────────────────────────────────────

@router.get("/{id}/historial")
def historial_cliente(id: int, db: Session = Depends(get_db)):
    """Estado de cuenta cronológico: compras y pagos mezclados con saldo acumulado."""
    c = db.query(Cliente).filter(Cliente.id == id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    fiados = db.query(Fiado).filter(Fiado.cliente_id == id).all()

    movimientos = []

    for f in fiados:
        # Armar descripción de la compra
        if f.venta_id:
            venta = db.query(Venta).filter(Venta.id == f.venta_id).first()
            if venta:
                items = db.query(ItemVenta, Producto).join(
                    Producto, ItemVenta.producto_id == Producto.id
                ).filter(ItemVenta.venta_id == venta.id).all()
                detalle = ", ".join(
                    f"{float(it.cantidad):g}x {pr.nombre}" for it, pr in items
                ) or "Venta"
                descripcion = f"Ticket #{venta.numero} — {detalle}"
            else:
                descripcion = f.descripcion or "Compra"
        else:
            descripcion = f.descripcion or "Compra registrada manualmente"

        movimientos.append({
            "fecha": str(f.created_at),
            "tipo": "compra",
            "descripcion": descripcion,
            "monto": float(f.monto),
        })

        # Pagos de este fiado
        for p in db.query(PagoFiado).filter(PagoFiado.fiado_id == f.id).all():
            movimientos.append({
                "fecha": str(p.fecha),
                "tipo": "pago",
                "descripcion": f"Pago — {(p.metodo or 'efectivo').capitalize()}" + (f" ({p.observacion})" if p.observacion else ""),
                "monto": float(p.monto),
            })

    # Ordenar cronológicamente
    movimientos.sort(key=lambda x: x["fecha"])

    # Calcular saldo acumulado
    saldo = 0.0
    for m in movimientos:
        if m["tipo"] == "compra":
            saldo += m["monto"]
        else:
            saldo -= m["monto"]
        m["saldo"] = round(saldo, 2)

    total_compras = sum(m["monto"] for m in movimientos if m["tipo"] == "compra")
    total_pagos   = sum(m["monto"] for m in movimientos if m["tipo"] == "pago")

    return {
        "cliente": {
            "id": c.id,
            "nombre": c.nombre,
            "puntos": float(c.puntos) if c.puntos else 0,
            "deuda_actual": float(c.deuda_actual) if c.deuda_actual else 0,
        },
        "movimientos": movimientos,
        "total_compras": total_compras,
        "total_pagos": total_pagos,
        "saldo_actual": round(total_compras - total_pagos, 2),
    }

@router.post("/{id}/canjear-puntos")
def canjear_puntos(id: int, db: Session = Depends(get_db)):
    """Canjea todos los puntos disponibles (en bloques de 100). 100 pts = $1000."""
    c = db.query(Cliente).filter(Cliente.id == id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    puntos = float(c.puntos) if c.puntos else 0
    if puntos < 100:
        raise HTTPException(
            status_code=400,
            detail=f"Mínimo 100 puntos para canjear. Tiene {puntos:.0f}"
        )
    bloques = int(puntos // 100)
    descuento = bloques * 1000
    puntos_usados = bloques * 100
    c.puntos = puntos - puntos_usados
    db.commit()
    db.refresh(c)
    return {
        "descuento": descuento,
        "puntos_usados": puntos_usados,
        "puntos_restantes": float(c.puntos)
    }

@router.post("/{id}/sumar-puntos")
def sumar_puntos(id: int, monto: float, db: Session = Depends(get_db)):
    """Suma puntos según el monto de compra. $100 = 1 punto."""
    c = db.query(Cliente).filter(Cliente.id == id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    puntos_nuevos = int(monto // 100)
    if puntos_nuevos > 0:
        c.puntos = (float(c.puntos) if c.puntos else 0) + puntos_nuevos
        db.commit()
        db.refresh(c)
    return {"puntos_sumados": puntos_nuevos, "puntos_total": float(c.puntos)}

@router.get("/{id}")
def obtener_cliente(id: int, db: Session = Depends(get_db)):
    c = db.query(Cliente).filter(Cliente.id == id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return c

@router.post("/")
def crear_cliente(datos: ClienteCrear, db: Session = Depends(get_db)):
    campos_modelo = {"nombre", "telefono", "email", "direccion", "fecha_nacimiento", "limite_credito", "notas"}
    data = {k: v for k, v in datos.dict().items() if k in campos_modelo and (v is not None or k == "limite_credito")}
    c = Cliente(**data)
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
        if hasattr(c, key):
            setattr(c, key, value)
    db.commit()
    db.refresh(c)
    return c

@router.delete("/{id}")
def eliminar_cliente(id: int, db: Session = Depends(get_db)):
    c = db.query(Cliente).filter(Cliente.id == id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    c.activo = False
    db.commit()
    return {"ok": True}