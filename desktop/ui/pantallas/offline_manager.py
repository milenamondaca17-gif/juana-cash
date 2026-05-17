"""
offline_manager.py — Modo offline robusto
Copiá a: desktop/ui/pantallas/offline_manager.py
"""
import json
import os
import requests
from datetime import datetime

COLA_PATH = os.path.join(os.path.expanduser("~"), "JuanaCash_Tickets", "cola_offline.json")
API_URL = "http://127.0.0.1:8000"


def _leer_cola():
    try:
        os.makedirs(os.path.dirname(COLA_PATH), exist_ok=True)
        if os.path.exists(COLA_PATH):
            with open(COLA_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return []


def _guardar_cola(cola):
    try:
        os.makedirs(os.path.dirname(COLA_PATH), exist_ok=True)
        with open(COLA_PATH, "w", encoding="utf-8") as f:
            json.dump(cola, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def servidor_disponible(timeout=2):
    """Verifica si el backend está respondiendo."""
    try:
        r = requests.get(f"{API_URL}/", timeout=timeout)
        return r.status_code == 200
    except Exception:
        return False


def encolar_venta(datos_venta: dict):
    """Guarda una venta en la cola offline."""
    cola = _leer_cola()
    datos_venta["_timestamp_offline"] = datetime.now().isoformat()
    datos_venta["_intentos"] = 0
    cola.append(datos_venta)
    _guardar_cola(cola)
    return len(cola)


def sincronizar_cola():
    """
    Intenta enviar todas las ventas en cola al servidor.
    Retorna (enviadas, fallidas, errores).
    """
    cola = _leer_cola()
    if not cola:
        return 0, 0, []

    enviadas = 0
    fallidas = 0
    errores = []
    cola_nueva = []

    for venta in cola:
        datos = {k: v for k, v in venta.items()
                 if not k.startswith("_")}
        try:
            r = requests.post(f"{API_URL}/ventas/", json=datos, timeout=5)
            if 200 <= r.status_code < 300:
                enviadas += 1
            else:
                fallidas += 1
                venta["_intentos"] = venta.get("_intentos", 0) + 1
                errores.append(f"Error {r.status_code}: {r.text[:50]}")
                if venta["_intentos"] < 5:
                    cola_nueva.append(venta)
        except Exception as e:
            fallidas += 1
            venta["_intentos"] = venta.get("_intentos", 0) + 1
            errores.append(str(e)[:50])
            if venta["_intentos"] < 5:
                cola_nueva.append(venta)

    _guardar_cola(cola_nueva)
    return enviadas, fallidas, errores


def cantidad_pendientes():
    """Retorna cuántas ventas hay en cola offline."""
    return len(_leer_cola())


def limpiar_cola():
    """Borra la cola offline."""
    _guardar_cola([])
