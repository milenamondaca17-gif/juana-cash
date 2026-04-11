from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from ..database import get_db
from ..models.usuario import Usuario
from ..config import SECRET_KEY, ALGORITHM, TOKEN_EXPIRE_MINUTOS

router = APIRouter(prefix="/auth", tags=["Autenticación"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class LoginEmail(BaseModel):
    email: str
    password: str

class LoginPin(BaseModel):
    pin: str

class UsuarioCrear(BaseModel):
    nombre: str
    email: str
    password: str
    rol: str = "cajero"

def crear_token(datos: dict):
    datos_copia = datos.copy()
    expira = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTOS)
    datos_copia.update({"exp": expira})
    return jwt.encode(datos_copia, SECRET_KEY, algorithm=ALGORITHM)

def verificar_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def hashear_password(password):
    return pwd_context.hash(password)

@router.post("/registro")
def registrar_usuario(datos: UsuarioCrear, db: Session = Depends(get_db)):
    existe = db.query(Usuario).filter(Usuario.email == datos.email).first()
    if existe:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    nuevo = Usuario(
        nombre=datos.nombre,
        email=datos.email,
        password_hash=hashear_password(datos.password),
        rol=datos.rol
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return {"mensaje": "Usuario creado", "id": nuevo.id, "nombre": nuevo.nombre}

@router.post("/login")
def login(datos: LoginEmail, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.email == datos.email).first()
    if not usuario or not verificar_password(datos.password, usuario.password_hash):
        raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")
    if not usuario.activo:
        raise HTTPException(status_code=403, detail="Usuario desactivado")
    token = crear_token({"sub": str(usuario.id), "rol": usuario.rol})
    return {"token": token, "nombre": usuario.nombre, "rol": usuario.rol}

@router.post("/login-pin")
def login_pin(datos: LoginPin, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(
        Usuario.pin == datos.pin,
        Usuario.activo == True
    ).first()
    if not usuario:
        raise HTTPException(status_code=401, detail="PIN incorrecto")
    token = crear_token({"sub": str(usuario.id), "rol": usuario.rol})
    return {"token": token, "nombre": usuario.nombre, "rol": usuario.rol}