from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import date
from ..database import get_db
from ..models.cliente import Cliente
from ..models.fiado import Fiado, PagoFiado

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
    """Historial de fiados y pagos de un cliente."""
    c = db.query(Cliente).filter(Cliente.id == id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    fiados = db.query(Fiado).filter(
        Fiado.cliente_id == id
    ).order_by(Fiado.created_at.desc()).all()
    historial = []
    for f in fiados:
        pagos_f = db.query(PagoFiado).filter(PagoFiado.fiado_id == f.id).all()
        historial.append({
            "id": f.id,
            "monto": float(f.monto),
            "saldo": float(f.saldo),
            "fecha": str(f.created_at),
            "estado": f.estado or "pendiente",
            "vencimiento": str(f.vencimiento) if f.vencimiento else None,
            "pagos": [
                {"monto": float(p.monto), "fecha": str(p.fecha), "metodo": p.metodo or "efectivo"}
                for p in pagos_f
            ]
        })
    return {
        "cliente": {
            "id": c.id,
            "nombre": c.nombre,
            "puntos": float(c.puntos) if c.puntos else 0,
            "deuda_actual": float(c.deuda_actual) if c.deuda_actual else 0
        },
        "historial": historial,
        "total_fiado": sum(float(f.monto) for f in fiados),
        "total_registros": len(fiados)
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
    data = {k: v for k, v in datos.dict().items() if k in campos_modelo and v is not None or k == "limite_credito"}
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
