from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import mysql.connector
from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

app = FastAPI()

# ✅ Función para conectar a la base de datos
def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

# ✅ Endpoint para verificar si un usuario está registrado
@app.get("/check_user/{phone_number}")
def check_user(phone_number: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT numero_celular FROM jugadores WHERE numero_celular = %s"
    cursor.execute(query, (phone_number,))
    user = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if user:
        return {"status": "registered"}
    else:
        return {"status": "not_registered"}

# ✅ Modelo de datos para registrar un usuario
class UserRegistration(BaseModel):
    phone_number: str
    alias: str
    sponsor: str

# ✅ Endpoint para registrar un nuevo usuario
@app.post("/register_user/")
def register_user(user: UserRegistration):
    conn = get_db_connection()
    cursor = conn.cursor()

    # 📌 Verificar si el número de celular o alias ya existen en la base de datos
    check_query = "SELECT numero_celular FROM jugadores WHERE numero_celular = %s OR alias = %s"
    cursor.execute(check_query, (user.phone_number, user.alias))
    existing_user = cursor.fetchone()

    if existing_user:
        cursor.close()
        conn.close()
        return JSONResponse(status_code=400, content={"error": "Número de celular o alias ya están registrados"})

    # 📌 Insertar el nuevo usuario
    insert_query = "INSERT INTO jugadores (numero_celular, alias, sponsor) VALUES (%s, %s, %s)"
    cursor.execute(insert_query, (user.phone_number, user.alias, user.sponsor))
    conn.commit()

    cursor.close()
    conn.close()

    return {"status": "success", "message": "Usuario registrado correctamente"}
