import sqlite3
from passlib.context import CryptContext

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
nueva_hash = pwd.hash("admin123")

conn = sqlite3.connect("juana_cash.db")
conn.execute("UPDATE usuarios SET password_hash = ? WHERE email = 'lucas@juanacash.com'", (nueva_hash,))
conn.commit()
print("Listo - Contraseña reseteada a: admin123")
conn.close()