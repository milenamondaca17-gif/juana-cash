import os
import sys
import json
import threading
import subprocess
import tempfile
import time
from datetime import datetime

GITHUB_USER  = "milenamondaca17-gif"
GITHUB_REPO  = "juana-cash"
TIMEOUT_RED  = 8

# ── Rutas ────────────────────────────────────────────────────────────────────
# version.json autoritative: donde lo pone el instalador (junto al .exe)
if getattr(sys, 'frozen', False):
    _BASE_DIR = os.path.dirname(sys.executable)
else:
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))

VERSION_FILE = os.path.join(_BASE_DIR, "version.json")

# Caché escribible en datos de usuario (nunca tiene problemas de permisos)
_DATA_DIR    = os.path.join(os.path.expanduser("~"), "JuanaCash_Data")
_CACHE_FILE  = os.path.join(_DATA_DIR, "version_installed.json")

LOG_FILE = os.path.join(_DATA_DIR, "juana_update.log")

# ── Log ──────────────────────────────────────────────────────────────────────
def _log(msg):
    try:
        os.makedirs(_DATA_DIR, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass

# ── SSL sin verificar (máquinas con certs desactualizados) ────────────────────
def _ssl_context():
    import ssl
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode    = ssl.CERT_NONE
    return ctx

# ── Versión local ─────────────────────────────────────────────────────────────
def leer_version_local():
    """
    Lee la versión real desde VERSION_FILE (puesto por el instalador).
    Fallback: caché de usuario si el archivo del instalador no existe.
    """
    # 1. Leer desde el archivo que pone el instalador
    for path in [VERSION_FILE, os.path.join(_BASE_DIR, "_internal", "version.json")]:
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    v = json.load(f).get("version", "0.0.0")
                _log(f"Version local leida: {v} (desde {path})")
                return v
        except Exception as e:
            _log(f"Error leyendo {path}: {e}")

    # 2. Fallback: caché de usuario
    try:
        if os.path.exists(_CACHE_FILE):
            with open(_CACHE_FILE, "r", encoding="utf-8") as f:
                v = json.load(f).get("version", "0.0.0")
            _log(f"Version local leida desde cache: {v}")
            return v
    except Exception as e:
        _log(f"Error leyendo cache: {e}")

    _log("No se pudo leer version local, usando 0.0.0")
    return "0.0.0"

def _guardar_cache(version):
    """Escribe la versión instalada en la carpeta del usuario (siempre escribible)."""
    try:
        os.makedirs(_DATA_DIR, exist_ok=True)
        with open(_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump({"version": version, "fecha": datetime.now().isoformat()}, f)
        _log(f"Cache version guardada: {version}")
    except Exception as e:
        _log(f"Error guardando cache: {e}")

# ── GitHub ────────────────────────────────────────────────────────────────────
def obtener_version_github():
    import urllib.request
    # Parámetro anti-caché para evitar que el CDN de GitHub devuelva versión vieja
    ts  = int(time.time())
    url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/version.json?t={ts}"
    _log(f"Consultando GitHub: {url}")
    try:
        req = urllib.request.urlopen(url, timeout=TIMEOUT_RED, context=_ssl_context())
        data = json.loads(req.read().decode())
        version       = data.get("version")
        installer_url = data.get("installer_url", "")
        _log(f"GitHub responde: version={version}, url={installer_url}")
        return version, installer_url
    except Exception as e:
        _log(f"Error consultando GitHub: {e}")
        return None, None

def version_mayor(v_nueva, v_actual):
    try:
        def partes(v): return [int(x) for x in v.split(".")]
        resultado = partes(v_nueva) > partes(v_actual)
        _log(f"Comparacion: {v_nueva} > {v_actual} = {resultado}")
        return resultado
    except Exception as e:
        _log(f"Error comparando versiones: {e}")
        return False

# ── Descarga e instalación ────────────────────────────────────────────────────
def descargar_e_instalar(installer_url, version_nueva,
                         callback_ok=None, callback_error=None,
                         callback_cerrar_app=None):
    import urllib.request
    try:
        tmp = tempfile.mktemp(suffix=".exe", prefix="JuanaCash_Update_")
        _log(f"Iniciando descarga de {installer_url} -> {tmp}")

        with urllib.request.urlopen(installer_url, context=_ssl_context()) as r:
            with open(tmp, "wb") as f:
                f.write(r.read())

        _log(f"Descarga completada. Tamanio: {os.path.getsize(tmp)} bytes")

        # Guardar en caché de usuario ANTES de lanzar el instalador
        _guardar_cache(version_nueva)

        _log(f"Ejecutando instalador: {tmp}")
        subprocess.Popen([tmp, "/VERYSILENT", "/NORESTART", "/CLOSEAPPLICATIONS"])
        _log("Instalador lanzado correctamente")

        if callback_ok:
            callback_ok(version_nueva)

        # Cerrar la app actual para que el instalador pueda reemplazar archivos sin bloqueos
        def _cerrar():
            time.sleep(2)
            if callback_cerrar_app:
                try:
                    callback_cerrar_app()
                except Exception:
                    pass
            else:
                _log("Cerrando app para que el instalador termine correctamente")
                os._exit(0)

        threading.Thread(target=_cerrar, daemon=True).start()

    except Exception as e:
        _log(f"Error en descarga/instalacion: {e}")
        if callback_error:
            callback_error(str(e))


# ── Clase principal ───────────────────────────────────────────────────────────
_ya_verificando = False

class Updater:
    def __init__(self):
        self.version_local = leer_version_local()
        # Sincronizar caché con la versión instalada real
        try:
            cache_ver = "0.0.0"
            if os.path.exists(_CACHE_FILE):
                with open(_CACHE_FILE, "r", encoding="utf-8") as f:
                    cache_ver = json.load(f).get("version", "0.0.0")
            # Usar el mayor entre archivo instalado y caché
            if version_mayor(cache_ver, self.version_local):
                self.version_local = cache_ver
                _log(f"Usando version de cache ({cache_ver}) por ser mas reciente")
        except Exception:
            pass

    def verificar(self,
                  on_preguntar=None,
                  on_descargando=None,
                  on_actualizado=None,
                  on_sin_internet=None,
                  on_no_hay_update=None,
                  on_cerrar_app=None):

        global _ya_verificando
        if _ya_verificando:
            _log("Ya hay una verificacion en curso, saliendo")
            return
        _ya_verificando = True

        def _check():
            global _ya_verificando
            try:
                _log("=== Inicio verificacion de actualizacion ===")
                version_github, installer_url = obtener_version_github()

                if version_github is None:
                    _log("Sin internet o error de red")
                    if on_sin_internet:
                        on_sin_internet()
                    return

                if not version_mayor(version_github, self.version_local):
                    _log("No hay actualizacion disponible")
                    if on_no_hay_update:
                        on_no_hay_update()
                    return

                _log(f"Actualizacion disponible: {self.version_local} -> {version_github}")

                confirmar = True
                if on_preguntar:
                    confirmar = on_preguntar(version_github)
                    _log(f"Confirmacion usuario: {confirmar}")

                if not confirmar:
                    return

                if on_descargando:
                    on_descargando(version_github)

                if installer_url:
                    descargar_e_instalar(
                        installer_url, version_github,
                        callback_ok=on_actualizado,
                        callback_error=lambda e: _log(f"callback_error: {e}"),
                        callback_cerrar_app=on_cerrar_app,
                    )
                else:
                    _log("Sin installer_url en version.json de GitHub")
                    if on_actualizado:
                        on_actualizado(version_github)

            except Exception as e:
                _log(f"Error inesperado en _check: {e}")
            finally:
                _ya_verificando = False
                _log("=== Fin verificacion ===")

        threading.Thread(target=_check, daemon=True).start()
