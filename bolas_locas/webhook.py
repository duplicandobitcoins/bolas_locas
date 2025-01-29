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

# ✅ Función para obtener tableros disponibles
def get_open_tableros():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id_tablero, nombre, precio_por_bolita FROM tableros WHERE estado = 'abierto'")
    tableros = cursor.fetchall()
    cursor.close()
    conn.close()
    return tableros

# ✅ Función para manejar la selección de "Jugar"
def handle_jugar(user_id):
    print("🎮 Acción detectada: Jugar")

    # Verificar si el usuario está registrado
    usuario = check_user_registered(user_id)
    if not usuario:
        return JSONResponse(content={"fulfillmentText": "❌ No estás registrado en el sistema."})

    # Obtener tableros abiertos
    tableros = get_open_tableros()
    if not tableros:
        return JSONResponse(content={"fulfillmentText": "🚧 No hay tableros disponibles en este momento."})

    mensaje = "🎲 *Selecciona un tablero para jugar:*"
    botones = {"inline_keyboard": []}

    for tablero in tableros:
        botones["inline_keyboard"].append([
            {"text": f"{tablero['nombre']} - 💰 {tablero['precio_por_bolita']}", "callback_data": f"tablero_{tablero['id_tablero']}"}
        ])

    return JSONResponse(content={
        "fulfillmentMessages": [
            {
                "platform": "TELEGRAM",
                "payload": {
                    "telegram": {
                        "parse_mode": "Markdown",
                        "text": mensaje,
                        "reply_markup": botones
                    }
                }
            }
        ]
    })

# ✅ Webhook de Dialogflow
@router.post("/webhook")
async def handle_dialogflow_webhook(request: Request):
    print("🚨 Webhook llamado") 
    data = await request.json()

    # ✅ Extraer el user_id de Telegram
    user_id = None
    try:
        user_id = data["originalDetectIntentRequest"]["payload"]["data"]["from"]["id"]
    except KeyError:
        try:
            user_id = data["originalDetectIntentRequest"]["payload"]["data"]["callback_query"]["from"]["id"]
            print(f"📌 User ID obtenido desde callback: {user_id}")
        except KeyError:
            return JSONResponse(content={"fulfillmentText": "❌ Error: No se pudo obtener el ID de usuario de Telegram."})

    # ✅ Verificar la acción
    action = data["queryResult"].get("action")

    if action == "actDatosCuenta":
        return handle_mi_cuenta(user_id)

    if action == "actCambiarNequi":
        rtaNuevoNequi = data["queryResult"]["parameters"].get("rtaNuevoNequi")
        return handle_cambiar_nequi(user_id, rtaNuevoNequi)

    if action == "actJugar":
        return handle_jugar(user_id)

    return JSONResponse(content={"fulfillmentText": "⚠️ Acción no reconocida."})

# ✅ Función para manejar "MiCuenta"
def handle_mi_cuenta(user_id):
    print("📌 Acción detectada: MiCuenta")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT numero_celular, alias, sponsor FROM jugadores WHERE user_id = %s", (user_id,))
    usuario = cursor.fetchone()
    cursor.close()
    conn.close()

    if not usuario:
        return JSONResponse(content={"fulfillmentText": "❌ No estás registrado en el sistema."})

    mensaje = (
        f"Tu cuenta en *Bolas Locas:*\n\n"
        f"👤 *Usuario:* _{usuario['alias']}_\n"
        f"📱 *Número registrado en Nequi:* _{usuario['numero_celular']}_\n"
        f"🤝 *Sponsor:* _{usuario['sponsor']}_\n\n"
        "🔽 ¿Qué quieres hacer?"
    )

    botones = {
        "fulfillmentMessages": [
            {
                "platform": "TELEGRAM",
                "payload": {
                    "telegram": {
                        "parse_mode": "Markdown",
                        "text": mensaje,
                        "reply_markup": {
                            "inline_keyboard": [
                                [{"text": "🔄 Cambiar número Nequi", "callback_data": "c4mb14r_n3qu1"}],
                                [{"text": "💰 Recargar saldo", "callback_data": "recargar_saldo"}],
                                [{"text": "🎮 Jugar", "callback_data": "jugar"}]
                            ]
                        }
                    }
                }
            }
        ]
    }

    return JSONResponse(content=botones)

# ✅ Función para manejar el cambio de número de Nequi
def handle_cambiar_nequi(user_id, rtaNuevoNequi):
    print("🔄 Acción detectada: CambiarNequi")

    # Validaciones del nuevo número de Nequi
    rtaNuevoNequi = re.sub(r"\D", "", str(rtaNuevoNequi))
    if not re.fullmatch(r"3\d{9}", rtaNuevoNequi):
        return JSONResponse(content={"fulfillmentText": "❌ El número de celular debe tener 10 dígitos y empezar por 3."})

    # Actualizar el número en la base de datos
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("UPDATE jugadores SET numero_celular = %s WHERE user_id = %s", (rtaNuevoNequi, user_id))
    conn.commit()
    cursor.close()
    conn.close()

    return JSONResponse(content={"fulfillmentText": "✅ Número de Nequi actualizado correctamente."})

    #######################
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
