from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
# Cambiá la línea de los modelos por esta:
from .models import Usuario, Producto, Venta, Cliente, Fiado, CajaTurno, SesionLog, Gasto
from .models import sesion_log, gasto
from .routers import (auth, productos, ventas, clientes, stock, ia, config_sistema,
                      reportes, caja, fiados, sesiones, gastos)
from .routers import ofertas_api

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Juana Cash API")

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

@app.get("/")
def root():
    return {"mensaje": "Juana Cash API funcionando ✅"}
