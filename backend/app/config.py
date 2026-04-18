# ============================================
# JUANA CASH - Configuración general
# ============================================
import os
import secrets

# Nombre de la app
APP_NAME = "Juana Cash"
APP_VERSION = "1.0.0"

# Base de datos (SQLite, archivo local)
DATABASE_URL = "sqlite:///./juana_cash.db"

# Seguridad
# La clave se lee de la variable de entorno JUANA_SECRET_KEY.
# Si no existe (primera vez), se genera una aleatoria y se guarda en un archivo local.
_KEY_FILE = os.path.join(os.path.dirname(__file__), "..", ".secret_key")

def _cargar_secret_key() -> str:
    # 1. Primero buscar en variable de entorno
    key_env = os.environ.get("JUANA_SECRET_KEY")
    if key_env:
        return key_env

    # 2. Buscar en archivo local .secret_key
    if os.path.exists(_KEY_FILE):
        with open(_KEY_FILE, "r") as f:
            key = f.read().strip()
            if key:
                return key

    # 3. Generar una nueva y guardarla (solo la primera vez)
    nueva_key = secrets.token_hex(32)
    try:
        with open(_KEY_FILE, "w") as f:
            f.write(nueva_key)
        print("✅ Clave secreta generada y guardada en .secret_key")
        print("   (No compartas ni subas ese archivo a GitHub)")
    except Exception:
        pass
    return nueva_key

SECRET_KEY = _cargar_secret_key()
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTOS = 480  # 8 horas

# Negocio
NOMBRE_NEGOCIO = "Mi Kiosco"
PUNTO_VENTA = 1
