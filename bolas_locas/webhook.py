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


# ✅ Función para verificar si un usuario ya está registrado
def check_user_registered(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT numero_celular FROM jugadores WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return result  # Retorna None si el usuario no está registrado
    
# ✅ Webhook de Dialogflow
@router.post("/webhook")
async def handle_dialogflow_webhook(request: Request):
    data = await request.json()

    # ✅ Extraer el user_id de Telegram
    try:
        user_id = data["originalDetectIntentRequest"]["payload"]["data"]["from"]["id"]
        print(f"User ID de Telegram: {user_id}")  # Para depuración
    except KeyError:
        print("❌ Error: No se pudo obtener el ID de usuario de Telegram.")
        return JSONResponse(content={"fulfillmentText": "Error: No se pudo obtener el ID de usuario de Telegram."})

    # ✅ Verificar si el usuario está registrado en la base de datos
    usuario = check_user_registered(user_id)

    if usuario:
        respuesta = "✅ Ya te encuentras registrado."
    else:
        respuesta = "❌ Aún no estás registrado."

    return JSONResponse(content={"fulfillmentText": respuesta})
