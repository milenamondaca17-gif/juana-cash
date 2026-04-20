"""
config_sistema.py — Configuración del sistema: sucursales, timeout, AFIP
Copiá a: backend/app/routers/config_sistema.py
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import json
import os

router = APIRouter(prefix="/config", tags=["Configuración"])

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "config_sistema.json")


def leer_config():
    defaults = {
        "negocio_nombre": "Juana Cash",
        "negocio_direccion": "",
        "negocio_telefono": "",
        "negocio_cuit": "",
        "negocio_iibb": "",
        "negocio_inicio_actividades": "",
        "negocio_condicion_iva": "Responsable Inscripto",
        "sucursal_actual": "1",
        "sucursales": [{"id": "1", "nombre": "Casa Central", "direccion": ""}],
        "timeout_minutos": 30,
        "modo_offline": True,
        "punto_venta": "0001",
        "afip_habilitado": False,
    }
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                defaults.update(data)
    except Exception:
        pass
    return defaults


def guardar_config(data: dict):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


class ConfigSistema(BaseModel):
    negocio_nombre: Optional[str] = None
    negocio_direccion: Optional[str] = None
    negocio_telefono: Optional[str] = None
    negocio_cuit: Optional[str] = None
    negocio_iibb: Optional[str] = None
    negocio_inicio_actividades: Optional[str] = None
    negocio_condicion_iva: Optional[str] = None
    sucursal_actual: Optional[str] = None
    timeout_minutos: Optional[int] = None
    modo_offline: Optional[bool] = None
    punto_venta: Optional[str] = None
    afip_habilitado: Optional[bool] = None


@router.get("/")
def obtener_config():
    return leer_config()


@router.put("/")
def actualizar_config(datos: ConfigSistema):
    config = leer_config()
    for key, value in datos.dict().items():
        if value is not None:
            config[key] = value
    if guardar_config(config):
        return {"ok": True, "config": config}
    raise HTTPException(status_code=500, detail="No se pudo guardar la configuración")


@router.get("/sucursales")
def listar_sucursales():
    return leer_config().get("sucursales", [])


class Sucursal(BaseModel):
    id: str
    nombre: str
    direccion: Optional[str] = ""


@router.post("/sucursales")
def agregar_sucursal(datos: Sucursal):
    config = leer_config()
    sucursales = config.get("sucursales", [])
    # Verificar que no exista
    if any(s["id"] == datos.id for s in sucursales):
        raise HTTPException(status_code=400, detail="Ya existe una sucursal con ese ID")
    sucursales.append(datos.dict())
    config["sucursales"] = sucursales
    guardar_config(config)
    return {"ok": True, "sucursales": sucursales}
