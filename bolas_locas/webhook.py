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

# ✅ Función para obtener el último usuario registrado
def get_last_registered_alias():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT alias FROM jugadores ORDER BY numero_celular DESC LIMIT 1")
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result["alias"] if result else None

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
        respuesta = "⚠️ATENCIÓN⚠️ El registro no pudo realizarse debido a que ésta cuenta de Telegram ya se encuentra registrada en el Juego Bolas Locas."
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

    # ✅ Verificar si se debe autoasignar el sponsor
    if rtaSponsor.lower() == "auto":
        rtaSponsor = get_last_registered_alias()
        if not rtaSponsor:
            error_message = "❌ No hay usuarios registrados para asignar como sponsor."
            print(error_message)
            return JSONResponse(content={
                "fulfillmentMessages": [{"text": {"text": [error_message]}}]
            }, status_code=200)
    else:
        # Verificar si el sponsor existe en la base de datos
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM jugadores WHERE alias = %s", (rtaSponsor,))
        sponsor_exists = cursor.fetchone()

        if not sponsor_exists:
            error_message = f"❌ Error: El usuario {rtaSponsor} de la persona que te invitó no existe. Por favor revisa si está bien escrito y vuelve a intentarlo."
            print(error_message)
            cursor.close()
            conn.close()
            return JSONResponse(content={
                "fulfillmentMessages": [{"text": {"text": [error_message]}}]
            }, status_code=200)
        cursor.close()
        conn.close()

    # ✅ Registrar al usuario en la base de datos
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "INSERT INTO jugadores (numero_celular, alias, sponsor, user_id) VALUES (%s, %s, %s, %s)",
            (rtaCelularNequi, rtaAlias, rtaSponsor, user_id)
        )
        conn.commit()
        print(f"✅ Usuario {rtaAlias} registrado correctamente con sponsor {rtaSponsor}.")
    except Exception as e:
        print(f"❌ Error al registrar el usuario: {e}")
        cursor.close()
        conn.close()
        return JSONResponse(content={"fulfillmentText": "Hubo un error al registrar al usuario."})

    cursor.close()
    conn.close()

    return JSONResponse(content={"fulfillmentText": f"✅ Usuario {rtaAlias} registrado correctamente con sponsor {rtaSponsor}."})


# ✅ Manejo del intento "MiCuenta"
if data["queryResult"]["action"] == "actDatosCuenta":
    print("📌 Acción detectada: MiCuenta")

    # Buscar datos del usuario en la base de datos
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT numero_celular, alias, sponsor FROM jugadores WHERE user_id = %s", (user_id,))
    usuario = cursor.fetchone()
    cursor.close()
    conn.close()

    if not usuario:
        return JSONResponse(content={"fulfillmentText": "❌ No estás registrado en el sistema."})

    # Construir mensaje con datos del usuario
    mensaje = (
        f"📋 *Tu cuenta en Bolas Locas:*\n"
        f"👤 *Alias:* {usuario['alias']}\n"
        f"📱 *Número registrado en Nequi:* {usuario['numero_celular']}\n"
        f"🤝 *Sponsor:* {usuario['sponsor']}\n\n"
        "🔽 ¿Qué quieres hacer?"
    )

    # Agregar botones de Telegram
    botones = {
        "fulfillmentMessages": [
            {
                "platform": "TELEGRAM",
                "payload": {
                    "telegram": {
                        "text": mensaje,
                        "reply_markup": {
                            "inline_keyboard": [
                                [{"text": "🔄 Cambiar número Nequi", "callback_data": "cambiar_nequi"}],
                                [{"text": "💰 Recargar saldo", "callback_data": "recargar_saldo"}]
                            ]
                        }
                    }
                }
            }
        ]
    }

    return JSONResponse(content=botones)

