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

# Migración: agrega columnas nuevas si no existen (SQLite no tiene IF NOT EXISTS en ALTER)
from sqlalchemy import text as _text
with engine.connect() as _conn:
    for _table, _col, _def in [
        ("caja_turnos", "pagos_empleados", "TEXT"),
        ("caja_turnos", "total_empleados",  "NUMERIC DEFAULT 0"),
        ("ventas",      "recargo",          "NUMERIC DEFAULT 0"),
        ("fiados",      "monto_pagado",     "NUMERIC DEFAULT 0"),
    ]:
        try:
            _conn.execute(_text(f"ALTER TABLE {_table} ADD COLUMN {_col} {_def}"))
            _conn.commit()
        except Exception:
            pass  # columna ya existe

app = FastAPI(title="Juana Cash API")

import traceback as _tb, os as _os, datetime as _datetime
_DATA_DIR = _os.path.join(_os.path.expanduser("~"), "JuanaCash_Data")

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

