from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import mysql.connector
import re  # Para validaciones
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
        respuesta = "⚠️ATENCIÓN⚠️ El registro no fue procesado debido a que ésta cuenta de Telegram ya se encuentra registrada en el Juego **Bolas Locas**."
        return JSONResponse(content={"fulfillmentText": respuesta})

    # ✅ Extraer los parámetros enviados desde Dialogflow
    rtaCelularNequi = data["queryResult"]["parameters"].get("rtaCelularNequi")
    rtaAlias = data["queryResult"]["parameters"].get("rtaAlias")
    rtaSponsor = data["queryResult"]["parameters"].get("rtaSponsor")

    print(f"Datos recibidos - Celular: {rtaCelularNequi}, Alias: {rtaAlias}, Sponsor: {rtaSponsor}")

    if not rtaCelularNequi or not rtaAlias or not rtaSponsor:
        print("❌ Error: Faltan parámetros obligatorios.")
        return JSONResponse(content={"fulfillmentText": "Faltan parámetros obligatorios."})

    # ✅ Validación del número de celular de Nequi
    rtaCelularNequi = re.sub(r"\D", "", str(rtaCelularNequi))  # Eliminar caracteres que no sean números
    
    if not re.fullmatch(r"3\d{9}", rtaCelularNequi):
        error_message = "❌ El número de celular debe tener 10 dígitos, empezar por 3 y no contener caracteres especiales."
        print(error_message)
        return JSONResponse(content={
            "fulfillmentMessages": [{"text": {"text": [error_message]}}]
        }, status_code=200)
    
    numero_celular = int(rtaCelularNequi)
    if numero_celular < 3000000000 or numero_celular > 3999999999:
        error_message = "❌ El número de celular debe estar entre 3000000000 y 3999999999."
        print(error_message)
        return JSONResponse(content={
            "fulfillmentMessages": [{"text": {"text": [error_message]}}]
        }, status_code=200)

    # Verificar si el alias ya existe
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM jugadores WHERE alias = %s", (rtaAlias,))
    existing_alias = cursor.fetchone()

    if existing_alias:
        print(f"❌ Error: El alias **{rtaAlias}** ya está registrado.")
        cursor.close()
        conn.close()
        return JSONResponse(content={"fulfillmentText": "❌ Error: El alias **{rtaAlias}** ya está registrado."})

    # Verificar si el sponsor existe en la base de datos
    cursor.execute("SELECT * FROM jugadores WHERE alias = %s", (rtaSponsor,))
    sponsor_exists = cursor.fetchone()

    if not sponsor_exists:
        error_message = f"❌ Error: El usuario de la persona que te invitó: **{rtaSponsor}** no existe.\n\nPor favor vuelve a intentarlo e ingresa un usuario válido."
        print(error_message)
        cursor.close()
        conn.close()
        return JSONResponse(content={
            "fulfillmentMessages": [{"text": {"text": [error_message]}}]
        }, status_code=200)

    # Si todo está bien, podemos continuar con el registro
    try:
        cursor.execute(
            "INSERT INTO jugadores (numero_celular, alias, sponsor, user_id) VALUES (%s, %s, %s, %s)",
            (rtaCelularNequi, rtaAlias, rtaSponsor, user_id)
        )
        conn.commit()
        print(f"✅ Usuario *{rtaAlias}* registrado correctamente.")
    except Exception as e:
        print(f"❌ Error al registrar el usuario: {e}")
        cursor.close()
        conn.close()
        return JSONResponse(content={"fulfillmentText": "Hubo un error al registrar al usuario."})

    cursor.close()
    conn.close()

    return JSONResponse(content={"fulfillmentText": "✅ Usuario *{rtaAlias}* registrado correctamente."})
