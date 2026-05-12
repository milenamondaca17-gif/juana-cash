from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
# CambiÃ¡ la lÃ­nea de los modelos por esta:
from .models import Usuario, Producto, Venta, Cliente, Fiado, CajaTurno, SesionLog, Gasto
from .models import sesion_log, gasto
from .routers import (auth, productos, ventas, clientes, stock, ia, config_sistema,
                      reportes, caja, fiados, sesiones, gastos)
from .routers import ofertas_api
from .routers import alertas
from .routers import cupones as cupones_router

import time as _time
for _intento in range(6):
    try:
        Base.metadata.create_all(bind=engine)
        break
    except Exception:
        if _intento == 5:
            raise
        _time.sleep(1)

# Migración: agrega columnas nuevas si no existen
from sqlalchemy import text as _text, inspect as _inspect
_inspector = _inspect(engine)
with engine.connect() as _conn:
    for _table, _col, _def in [
        ("caja_turnos", "pagos_empleados", "TEXT"),
        ("caja_turnos", "total_empleados",  "NUMERIC DEFAULT 0"),
        ("ventas",      "recargo",          "NUMERIC DEFAULT 0"),
        ("fiados",      "monto_pagado",     "NUMERIC DEFAULT 0"),
    ]:
        try:
            tablas = _inspector.get_table_names()
            if _table not in tablas:
                continue
            cols = [c["name"] for c in _inspector.get_columns(_table)]
            if _col not in cols:
                _conn.execute(_text(f"ALTER TABLE {_table} ADD COLUMN {_col} {_def}"))
                _conn.commit()
        except Exception:
            pass

app = FastAPI(title="Juana Cash API")

import traceback as _tb, os as _os, datetime as _datetime, json as _json, sys as _sys
_DATA_DIR = _os.path.join(_os.path.expanduser("~"), "JuanaCash_Data")

# ── Aplicar precios_update.json al inicio si hay versión nueva ────────────────
def _aplicar_precios_update():
    try:
        if getattr(_sys, "frozen", False):
            _base = _os.path.dirname(_sys.executable)
        else:
            _base = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
        _archivo = _os.path.join(_base, "precios_update.json")
        if not _os.path.exists(_archivo):
            return
        with open(_archivo, "r", encoding="utf-8") as _f:
            _data = _json.load(_f)
        _version = str(_data.get("version", ""))
        _applied = _os.path.join(_DATA_DIR, "precios_applied.txt")
        if _os.path.exists(_applied):
            with open(_applied, "r") as _f:
                if _f.read().strip() == _version:
                    return
        from .config import DATABASE_URL as _DB_URL
        import sqlite3 as _sq
        _db_path = _DB_URL.replace("sqlite:///", "")
        _conn = _sq.connect(_db_path)
        _cur = _conn.cursor()
        _por_cod = {}
        _por_nom = {}
        for _r in _cur.execute("SELECT id, codigo_barra, nombre FROM productos"):
            _pid, _cod, _nom = _r
            if _cod: _por_cod[str(_cod)] = _pid
            if _nom: _por_nom[_nom.lower().strip()] = _pid
        _upd = _ins = 0
        for _p in _data.get("productos", []):
            _nom = (_p.get("nombre") or "").strip()
            _cod = _p.get("codigo") or None
            _pv  = float(_p.get("precio_venta") or 0)
            _pc  = float(_p.get("precio_costo") or 0) or None
            if not _nom or _pv <= 0:
                continue
            _pid = None
            if _cod and str(_cod) in _por_cod:
                _pid = _por_cod[str(_cod)]
            elif _nom.lower().strip() in _por_nom:
                _pid = _por_nom[_nom.lower().strip()]
            if _pid:
                _cur.execute("UPDATE productos SET precio_venta=?, precio_costo=? WHERE id=?", (_pv, _pc, _pid))
                _upd += 1
            else:
                _cur.execute("INSERT INTO productos (nombre, codigo_barra, precio_venta, precio_costo, stock_actual, activo) VALUES (?,?,?,?,0,1)", (_nom, _cod, _pv, _pc))
                _nuevo = _cur.lastrowid
                _por_nom[_nom.lower().strip()] = _nuevo
                if _cod: _por_cod[str(_cod)] = _nuevo
                _ins += 1
        _conn.commit()
        _conn.close()
        with open(_applied, "w") as _f:
            _f.write(_version)
        print(f"Precios aplicados: {_upd} actualizados, {_ins} nuevos")
    except Exception as _e:
        print(f"Error al aplicar precios: {_e}")

_aplicar_precios_update()
# ─────────────────────────────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def _handler_global(request, exc):
    from fastapi.responses import JSONResponse
    msg = f"{type(exc).__name__}: {exc}"
    try:
        with open(_os.path.join(_DATA_DIR, "debug.log"), "a") as _f:
            _f.write(f"\n[{_datetime.datetime.now()}] ERROR en {request.url.path}\n{msg}\n{_tb.format_exc()}\n")
    except Exception:
        pass
    return JSONResponse(status_code=500, content={"detail": msg})

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(productos.router)
app.include_router(ventas.router)
app.include_router(clientes.router)
app.include_router(reportes.router)
app.include_router(caja.router)
app.include_router(fiados.router)
app.include_router(sesiones.router)
app.include_router(gastos.router)
app.include_router(stock.router)
app.include_router(ia.router)
app.include_router(config_sistema.router)
app.include_router(ofertas_api.router)
app.include_router(alertas.router)
app.include_router(cupones_router.router)

@app.get("/")
def root():
    return {"mensaje": "Juana Cash API funcionando âœ…"}

