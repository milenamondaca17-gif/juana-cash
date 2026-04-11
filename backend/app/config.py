# ============================================
# JUANA CASH - Configuración general
# ============================================

# Nombre de la app
APP_NAME = "Juana Cash"
APP_VERSION = "1.0.0"

# Base de datos (SQLite, archivo local)
DATABASE_URL = "sqlite:///./juana_cash.db"

# Seguridad
SECRET_KEY = "juana-cash-clave-secreta-2026"
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTOS = 480  # 8 horas

# Negocio
NOMBRE_NEGOCIO = "Mi Kiosco"
PUNTO_VENTA = 1