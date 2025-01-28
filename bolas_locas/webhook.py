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
    
    # 🔹 Mostrar el JSON completo en los logs de Railway
    print("📌 Webhook recibido:", data)

    # 📌 Extraer Intent y Action
    intent_name = data["queryResult"]["intent"]["displayName"]
    action = data["queryResult"]["action"]

    # 📌 Intent esperado
    if intent_name == "RegistroUsuario" and action == "actRegistrarUsuario":
        try:
            # 🔹 Verificar si "originalDetectIntentRequest" tiene la estructura esperada
            user_id = data["originalDetectIntentRequest"]["payload"]["data"]["message"]["from"]["id"]
            print(f"✅ ID de usuario obtenido: {user_id}")
        except KeyError:
            return JSONResponse(content={"fulfillmentText": "Error: No se pudo obtener el ID de usuario de Telegram."}, status_code=200)

        # 🔹 Verificar si el usuario ya está registrado
        user = check_user_registered(user_id)
        response_text = "Ya estás registrado." if user else "Aún no estás registrado."
        
        return JSONResponse(content={"fulfillmentText": response_text}, status_code=200)

    return JSONResponse(content={"fulfillmentText": "No se reconoce el intento."}, status_code=200)
