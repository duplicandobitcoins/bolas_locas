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
        # Si el usuario ya está registrado, respondemos con un mensaje y no hacemos más validaciones
        respuesta = "✅ Esta cuenta de Telegram ya se encuentra registrada en el Juego Bolas Locas."
        return JSONResponse(content={"fulfillmentText": respuesta})

    # ✅ Si el usuario no está registrado, continuamos con las validaciones de alias y sponsor
    # Extraemos los parámetros enviados desde Dialogflow
    rtaCelularNequi = data["queryResult"]["parameters"].get("rtaCelularNequi")
    rtaAlias = data["queryResult"]["parameters"].get("rtaAlias")
    rtaSponsor = data["queryResult"]["parameters"].get("rtaSponsor")

    if not rtaCelularNequi or not rtaAlias or not rtaSponsor:
        return JSONResponse(status_code=400, content={"error": "Faltan parámetros obligatorios."})

    # Verificar si el alias ya existe
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Verificar si el alias existe en la base de datos
    cursor.execute("SELECT * FROM jugadores WHERE alias = %s", (rtaAlias,))
    existing_alias = cursor.fetchone()

    if existing_alias:
        cursor.close()
        conn.close()
        return JSONResponse(status_code=400, content={"error": "El alias ya está registrado."})

    # Verificar si el sponsor existe en la base de datos
    cursor.execute("SELECT * FROM jugadores WHERE alias = %s", (rtaSponsor,))
    sponsor_exists = cursor.fetchone()

    if not sponsor_exists:
        cursor.close()
        conn.close()
        return JSONResponse(status_code=400, content={"error": "El sponsor no existe. Por favor ingresa un sponsor válido."})

    # Si todo está bien, podemos continuar con el registro
    cursor.execute(
        "INSERT INTO jugadores (numero_celular, alias, sponsor, user_id) VALUES (%s, %s, %s, %s)",
        (rtaCelularNequi, rtaAlias, rtaSponsor, user_id)
    )
    conn.commit()

    cursor.close()
    conn.close()

    # Responder que el usuario fue registrado
    return JSONResponse(content={"fulfillmentText": "✅ Usuario registrado correctamente."})
