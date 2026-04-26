"""
updater.py — Auto-updater para Juana Cash
Se llama al arrancar. Compara versión local con GitHub.
Si hay update disponible, pregunta al usuario UNA SOLA VEZ.
Si no hay internet, arranca normal sin molestar.
"""
import os
import sys
import json
import threading
import subprocess
import tempfile
import time

GITHUB_USER  = "milenamondaca17-gif"
GITHUB_REPO  = "juana-cash"
VERSION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "version.json")
TIMEOUT_RED  = 4

# ── Evitar doble ejecución ────────────────────────────────────────────────────
_ya_verificando = False

def leer_version_local():
    try:
        if os.path.exists(VERSION_FILE):
            with open(VERSION_FILE, "r") as f:
                return json.load(f).get("version", "0.0.0")
    except Exception:
        pass
    return "0.0.0"

def guardar_version_local(version):
    try:
        with open(VERSION_FILE, "w") as f:
            json.dump({"version": version}, f)
    except Exception:
        pass

def obtener_version_github():
    import urllib.request
    url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/version.json"
    try:
        req = urllib.request.urlopen(url, timeout=TIMEOUT_RED)
        data = json.loads(req.read().decode())
        return data.get("version"), data.get("installer_url", "")
    except Exception:
        return None, None

def version_mayor(v_nueva, v_actual):
    try:
        def partes(v): return [int(x) for x in v.split(".")]
        return partes(v_nueva) > partes(v_actual)
    except Exception:
        return False

def descargar_e_instalar(installer_url, version_nueva, callback_ok=None, callback_error=None):
    import urllib.request
    try:
        tmp = tempfile.mktemp(suffix=".exe", prefix="JuanaCash_Update_")
        urllib.request.urlretrieve(installer_url, tmp)
        guardar_version_local(version_nueva)
        # /SILENT evita la segunda ventana del instalador
        subprocess.Popen([tmp, "/SILENT", "/NORESTART", "/CLOSEAPPLICATIONS"])
        if callback_ok:
            callback_ok(version_nueva)
    except Exception as e:
        if callback_error:
            callback_error(str(e))


class Updater:
    """
    Uso desde splash.py:
        u = Updater()
        u.verificar(
            on_preguntar   = lambda v: True/False,   # pregunta al usuario
            on_descargando = lambda v: ...,
            on_actualizado = lambda v: ...,
            on_sin_internet= lambda: ...,
            on_no_hay_update= lambda: ...,
        )
    """
    def __init__(self):
        self.version_local = leer_version_local()

    def verificar(self,
                  on_preguntar=None,
                  on_descargando=None,
                  on_actualizado=None,
                  on_sin_internet=None,
                  on_no_hay_update=None):

        global _ya_verificando
        # PROTECCIÓN: si ya se está verificando no arrancar otro hilo
        if _ya_verificando:
            return
        _ya_verificando = True

        def _check():
            global _ya_verificando
            try:
                version_github, installer_url = obtener_version_github()

                if version_github is None:
                    if on_sin_internet:
                        on_sin_internet()
                    return

                if not version_mayor(version_github, self.version_local):
                    if on_no_hay_update:
                        on_no_hay_update()
                    return

                # Hay actualización — preguntar UNA sola vez
                confirmar = True
                if on_preguntar:
                    confirmar = on_preguntar(version_github)

                if not confirmar:
                    return

                if on_descargando:
                    on_descargando(version_github)

                if installer_url:
                    descargar_e_instalar(
                        installer_url, version_github,
                        callback_ok=on_actualizado,
                        callback_error=lambda e: print(f"Error update: {e}")
                    )
                else:
                    if on_actualizado:
                        on_actualizado(version_github)
            finally:
                _ya_verificando = False

        threading.Thread(target=_check, daemon=True).start()
