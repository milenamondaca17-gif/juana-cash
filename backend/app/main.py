from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .models import usuario, producto, venta, cliente, fiado, caja_turno
from .models import sesion_log, gasto
from .routers import (auth, productos, ventas, clientes,
                      reportes, caja, fiados, sesiones, gastos)

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

@app.get("/")
def root():
    return {"mensaje": "Juana Cash API funcionando ✅"}