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
VERSION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "version.json")
TIMEOUT_RED  = 8

LOG_FILE = os.path.join(os.path.expanduser("~"), "Desktop", "juana_update.log")

def _log(msg):
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass

_ya_verificando = False

def leer_version_local():
    try:
        if os.path.exists(VERSION_FILE):
            with open(VERSION_FILE, "r") as f:
                v = json.load(f).get("version", "0.0.0")
                _log(f"Version local leida: {v} (desde {VERSION_FILE})")
                return v
    except Exception as e:
        _log(f"Error leyendo version local: {e}")
    return "0.0.0"

def guardar_version_local(version):
    try:
        with open(VERSION_FILE, "w") as f:
            json.dump({"version": version}, f)
        _log(f"Version local guardada: {version}")
    except Exception as e:
        _log(f"Error guardando version local: {e}")

def _ssl_context():
    import ssl
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx

def obtener_version_github():
    import urllib.request
    url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/version.json"
    _log(f"Consultando GitHub: {url}")
    try:
        req = urllib.request.urlopen(url, timeout=TIMEOUT_RED, context=_ssl_context())
        data = json.loads(req.read().decode())
        version = data.get("version")
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

def descargar_e_instalar(installer_url, version_nueva, callback_ok=None, callback_error=None):
    import urllib.request
    try:
        tmp = tempfile.mktemp(suffix=".exe", prefix="JuanaCash_Update_")
        _log(f"Iniciando descarga de {installer_url} -> {tmp}")
        with urllib.request.urlopen(installer_url, context=_ssl_context()) as r:
            with open(tmp, "wb") as f:
                f.write(r.read())
        _log(f"Descarga completada. Tamanio: {os.path.getsize(tmp)} bytes")
        guardar_version_local(version_nueva)
        _log(f"Ejecutando instalador: {tmp}")
        subprocess.Popen([tmp, "/SILENT", "/NORESTART", "/CLOSEAPPLICATIONS"])
        _log("Instalador lanzado correctamente")
        if callback_ok:
            callback_ok(version_nueva)
    except Exception as e:
        _log(f"Error en descarga/instalacion: {e}")
        if callback_error:
            callback_error(str(e))


class Updater:
    def __init__(self):
        self.version_local = leer_version_local()

    def verificar(self,
                  on_preguntar=None,
                  on_descargando=None,
                  on_actualizado=None,
                  on_sin_internet=None,
                  on_no_hay_update=None):

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
                        callback_error=lambda e: _log(f"callback_error: {e}")
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
