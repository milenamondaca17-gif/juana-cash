"""
ofertas_api.py — Endpoints para gestionar ofertas desde cualquier dispositivo
"""
import os
import json
import shutil
import urllib.request
import urllib.parse
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/ofertas", tags=["Ofertas"])

OFERTAS_PATH = os.path.join(os.path.expanduser("~"), "JuanaCash_Tickets", "ofertas.json")
IMAGENES_DIR = os.path.join(os.path.expanduser("~"), "JuanaCash_Tickets", "imagenes_ofertas")


def _leer():
    try:
        os.makedirs(os.path.dirname(OFERTAS_PATH), exist_ok=True)
        if os.path.exists(OFERTAS_PATH):
            with open(OFERTAS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return []


def _guardar(ofertas):
    try:
        os.makedirs(os.path.dirname(OFERTAS_PATH), exist_ok=True)
        with open(OFERTAS_PATH, "w", encoding="utf-8") as f:
            json.dump(ofertas, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


class OfertaTexto(BaseModel):
    contenido: str
    color_fondo: Optional[str] = "#e74c3c"
    color_texto: Optional[str] = "#ffffff"
    tamanio: Optional[int] = 32


@router.get("/")
def listar_ofertas():
    """Devuelve todas las ofertas actuales."""
    return _leer()


@router.post("/texto")
def agregar_texto(datos: OfertaTexto):
    """Agrega una oferta de texto desde cualquier dispositivo."""
    if not datos.contenido.strip():
        raise HTTPException(status_code=400, detail="El contenido no puede estar vacío")
    ofertas = _leer()
    ofertas.append({
        "tipo":        "texto",
        "contenido":   datos.contenido.strip(),
        "color_fondo": datos.color_fondo,
        "color_texto": datos.color_texto,
        "tamanio":     datos.tamanio
    })
    _guardar(ofertas)
    return {"ok": True, "total": len(ofertas)}


class OfertaImagenUrl(BaseModel):
    url: str

@router.post("/imagen-url")
def agregar_imagen_por_url(datos: OfertaImagenUrl):
    """Descarga una imagen desde una URL y la agrega como oferta."""
    url = datos.url.strip()
    if not url.startswith("http"):
        raise HTTPException(status_code=400, detail="URL inválida — debe empezar con http")

    os.makedirs(IMAGENES_DIR, exist_ok=True)

    parsed = urllib.parse.urlparse(url)
    ext = os.path.splitext(parsed.path)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png", ".webp", ".bmp"]:
        ext = ".jpg"

    nombre_seguro = f"oferta_{len(_leer())+1:03d}{ext}"
    ruta_destino  = os.path.join(IMAGENES_DIR, nombre_seguro)

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            with open(ruta_destino, "wb") as f:
                shutil.copyfileobj(resp, f)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"No se pudo descargar la imagen: {e}")

    ofertas = _leer()
    ofertas.append({"tipo": "imagen", "contenido": ruta_destino})
    _guardar(ofertas)
    return {"ok": True, "ruta": nombre_seguro, "total": len(ofertas)}


@router.post("/imagen")
async def subir_imagen(archivo: UploadFile = File(...)):
    """Sube una imagen desde el celular y la agrega como oferta."""
    os.makedirs(IMAGENES_DIR, exist_ok=True)

    # Validar que sea imagen
    ext = os.path.splitext(archivo.filename)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png", ".webp", ".bmp"]:
        raise HTTPException(status_code=400, detail="Solo se aceptan imágenes (jpg, png, webp)")

    # Guardar el archivo
    nombre_seguro = f"oferta_{len(_leer())+1:03d}{ext}"
    ruta_destino  = os.path.join(IMAGENES_DIR, nombre_seguro)
    with open(ruta_destino, "wb") as f:
        shutil.copyfileobj(archivo.file, f)

    # Agregar a ofertas
    ofertas = _leer()
    ofertas.append({"tipo": "imagen", "contenido": ruta_destino})
    _guardar(ofertas)
    return {"ok": True, "ruta": ruta_destino, "total": len(ofertas)}


@router.delete("/{idx}")
def eliminar_oferta(idx: int):
    """Elimina la oferta en la posición idx."""
    ofertas = _leer()
    if idx < 0 or idx >= len(ofertas):
        raise HTTPException(status_code=404, detail="Oferta no encontrada")
    oferta = ofertas.pop(idx)
    # Si era imagen, borrar el archivo si está en nuestra carpeta
    if oferta.get("tipo") == "imagen":
        ruta = oferta.get("contenido", "")
        if IMAGENES_DIR in ruta and os.path.exists(ruta):
            try:
                os.remove(ruta)
            except Exception:
                pass
    _guardar(ofertas)
    return {"ok": True, "total": len(ofertas)}


@router.delete("/")
def limpiar_ofertas():
    """Borra todas las ofertas."""
    _guardar([])
    return {"ok": True}
