import os
import json

_DATA_DIR    = os.path.join(os.path.expanduser("~"), "JuanaCash_Data")
_TICKET_CFG  = os.path.join(_DATA_DIR, "ticket_config.json")
_APP_CFG     = os.path.join(_DATA_DIR, "app_config.json")

# Fallback: solo se usa en la PC original si no hay config guardada
_NUMEROS_FALLBACK = ["2634670678", "2634633099", "2634633067"]


def leer_nombre_negocio() -> str:
    try:
        if os.path.exists(_TICKET_CFG):
            with open(_TICKET_CFG, "r", encoding="utf-8") as f:
                nombre = json.load(f).get("nombre_negocio", "")
                if nombre:
                    return nombre
    except Exception:
        pass
    return "JUANA CASH"


def leer_numeros_reporte() -> list:
    try:
        if os.path.exists(_APP_CFG):
            with open(_APP_CFG, "r", encoding="utf-8") as f:
                nums = json.load(f).get("numeros_reportes", [])
                nums = [n.strip() for n in nums if n.strip()]
                if nums:
                    return nums
    except Exception:
        pass
    return _NUMEROS_FALLBACK


def guardar_numeros_reporte(numeros: list):
    os.makedirs(_DATA_DIR, exist_ok=True)
    cfg = {}
    try:
        if os.path.exists(_APP_CFG):
            with open(_APP_CFG, "r", encoding="utf-8") as f:
                cfg = json.load(f)
    except Exception:
        pass
    cfg["numeros_reportes"] = [n.strip() for n in numeros if n.strip()]
    with open(_APP_CFG, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
