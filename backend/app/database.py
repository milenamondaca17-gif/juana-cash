# ============================================
# JUANA CASH - Conexión a la base de datos
# ============================================

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import DATABASE_URL

# Crear el motor de base de datos
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Necesario para SQLite
)

# Crear sesiones para hablar con la base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Clase base para todos los modelos
Base = declarative_base()

# Función para obtener una sesión (se usa en cada endpoint)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()