from fastapi import APIRouter, Request
import mysql.connector
import os

router = APIRouter()

# Configuración de la base de datos en Railway
db_config = {
    "host": os.getenv("MYSQLHOST", "mysql.railway.internal"),
    "user": os.getenv("MYSQLUSER", "root"),
    "password": os.getenv("MYSQLPASSWORD", "gipLtWlfZfkaopbYuWSfKmbnxxwQuhLZ"),
    "database": os.getenv("MYSQLDATABASE", "railway"),
}

# Función para verificar si un usuario ya está registrado
def check_user_registered(phone_number):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT numero_celular, alias FROM jugadores WHERE numero_celular = %s", (phone_number,))
        result = cursor.fetchone()
        conn.close()
        return result  # Retorna None si no está registrado, o el usuario si existe
    except Exception as e:
        print(f"Error en la base de datos: {e}")
        return None

@router.post("/webhook")
async def dialogflow_webhook(request: Request):
    data = await request.json()

    # 📌 Capturar el user_id automáticamente
    user_id = data.get("originalDetectIntentRequest", {}).get("payload", {}).get("data", {}).get("from", {}).get("id")

    intent_name = data.get("queryResult", {}).get("intent", {}).get("displayName")

    if not user_id:
        return {"fulfillmentText": "No pude obtener tu identificación de usuario en Telegram."}

    # Verificar si el usuario ya está registrado
    user = check_user_registered(user_id)

    if user:
        return {"fulfillmentText": f"Ya te encuentras registrado con el alias {user['alias']}."}

    # Si no está registrado, pedir el número de teléfono
    response = {
        "fulfillmentMessages": [
            {
                "text": {
                    "text": [f"Deseas registrar el usuario {user_id} en el juego Bolas Locas?"]
                }
            },
            {
                "payload": {
                    "telegram": {
                        "reply_markup": {
                            "inline_keyboard": [
                                [
                                    {"text": "SI", "callback_data": "S1R3g1B0l4L0c4"},
                                    {"text": "NO", "callback_data": "N0R3g1B0l4L0c4"}
                                ]
                            ]
                        }
                    }
                }
            }
        ]
    }
    return response


    return {"fulfillmentText": "No entiendo esa solicitud."}
