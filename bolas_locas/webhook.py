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
    print("🚨 Webhook llamado") 
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
        return JSONResponse(content={
            "fulfillmentMessages": [
                {"text": {"text": ["✅ Esta cuenta de Telegram ya se encuentra registrada en el Juego Bolas Locas."]}}
            ]
        })

    # ✅ Si el usuario no está registrado, continuamos con las validaciones de alias y sponsor
    # Extraemos los parámetros enviados desde Dialogflow
    rtaCelularNequi = data["queryResult"]["parameters"].get("rtaCelularNequi")
    rtaAlias = data["queryResult"]["parameters"].get("rtaAlias")
    rtaSponsor = data["queryResult"]["parameters"].get("rtaSponsor")

    print(f"Datos recibidos - Celular: {rtaCelularNequi}, Alias: {rtaAlias}, Sponsor: {rtaSponsor}")  # Para depuración

    if not rtaCelularNequi or not rtaAlias or not rtaSponsor:
        return JSONResponse(content={
            "fulfillmentMessages": [
                {"text": {"text": ["❌ Error: Faltan parámetros obligatorios."]}}
            ]
        })

    # ✅ Conectar a la base de datos
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # ✅ Verificar si el alias ya está registrado
    cursor.execute("SELECT * FROM jugadores WHERE alias = %s", (rtaAlias,))
    existing_alias = cursor.fetchone()

    if existing_alias:
        print(f"❌ Error: El alias {rtaAlias} ya está registrado.")  # Para depuración
        cursor.close()
        conn.close()
        return JSONResponse(content={
            "fulfillmentMessages": [
                {"text": {"text": [f"❌ Error: El alias {rtaAlias} ya está registrado."]}}
            ]
        })

    # ✅ Verificar si el sponsor existe en la base de datos
    cursor.execute("SELECT * FROM jugadores WHERE alias = %s", (rtaSponsor,))
    sponsor_exists = cursor.fetchone()

    if not sponsor_exists:
        error_message = f"❌ Error: El sponsor {rtaSponsor} no existe. Por favor ingresa un sponsor válido."
        print(error_message)  # Para depuración
        
        cursor.close()
        conn.close()
        
        # 🔹 Enviar la respuesta correctamente a Dialogflow
        return JSONResponse(content={
            "fulfillmentMessages": [
                {"text": {"text": [error_message]}}
            ]
        })

    # ✅ Si todo está bien, podemos continuar con el registro
    try:
        cursor.execute(
            "INSERT INTO jugadores (numero_celular, alias, sponsor, user_id) VALUES (%s, %s, %s, %s)",
            (rtaCelularNequi, rtaAlias, rtaSponsor, user_id)
        )
        conn.commit()
        print(f"✅ Usuario {rtaAlias} registrado correctamente.")  # Para depuración
    except Exception as e:
        print(f"❌ Error al registrar el usuario: {e}")  # Para depuración
        cursor.close()
        conn.close()
        return JSONResponse(content={
            "fulfillmentMessages": [
                {"text": {"text": ["❌ Hubo un error al registrar al usuario."]}}
            ]
        })

    cursor.close()
    conn.close()

    # ✅ Responder que el usuario fue registrado correctamente
    return JSONResponse(content={
        "fulfillmentMessages": [
            {"text": {"text": ["✅ Usuario registrado correctamente. ¡Bienvenido a Bolas Locas!"]}}
        ]
    })
