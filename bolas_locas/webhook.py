from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import mysql.connector
from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

router = APIRouter()

# ✅ Función para conectar a la base de datos
def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

# ✅ Función para verificar si el usuario está registrado
def check_user_registered(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    query = "SELECT numero_celular FROM jugadores WHERE user_id = %s"
    cursor.execute(query, (user_id,))
    result = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    return result  # Retorna None si no está registrado

# ✅ Webhook de Dialogflow
@router.post("/webhook")
async def handle_dialogflow_webhook(request: Request):
    data = await request.json()

    # Extrae el user_id de Telegram desde la estructura de datos
    try:
        user_id = data["originalDetectIntentRequest"]["payload"]["data"]["from"]["id"]
        print(f"User ID de Telegram: {user_id}")  # Para ver si todo está funcionando correctamente
    except KeyError:
        print("Error: No se pudo obtener el ID de usuario de Telegram.")
        return JSONResponse(content={"fulfillmentText": "Error: No se pudo obtener el ID de usuario de Telegram."})

    # Aquí va la lógica para verificar si el usuario está registrado o no
    # ...

    return JSONResponse(content={"fulfillmentText": "Recibido en webhook"})
