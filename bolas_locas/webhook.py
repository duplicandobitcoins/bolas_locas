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

# ✅ Función para registrar un usuario
def handle_registrar_usuario(user_id, data):
    print("📝 Acción detectada: Registro de Usuario")

    # ✅ Verificar si el usuario ya está registrado
    usuario = check_user_registered(user_id)
    if usuario:
        return JSONResponse(content={"fulfillmentText": "⚠️ Esta cuenta de Telegram ya está registrada en el Juego Bolas Locas."})

    # ✅ Extraer los parámetros enviados desde Dialogflow
    rtaCelularNequi = data["queryResult"]["parameters"].get("rtaCelularNequi", "").strip()
    rtaAlias = data["queryResult"]["parameters"].get("rtaAlias", "").strip()
    rtaSponsor = data["queryResult"]["parameters"].get("rtaSponsor", "").strip()

    print(f"📌 Datos recibidos - Celular: {rtaCelularNequi}, Alias: {rtaAlias}, Sponsor: {rtaSponsor}")

    # ✅ Validación de parámetros obligatorios
    if not rtaCelularNequi or not rtaAlias or not rtaSponsor:
        return JSONResponse(content={"fulfillmentText": "❌ Faltan parámetros obligatorios. Verifica la información ingresada."})

    # ✅ Validación del número de celular de Nequi
    rtaCelularNequi = re.sub(r"\D", "", rtaCelularNequi)  # Eliminar caracteres no numéricos
    if not re.fullmatch(r"3\d{9}", rtaCelularNequi):
        return JSONResponse(content={"fulfillmentText": "❌ El número de celular debe tener 10 dígitos y empezar por 3."})

    # ✅ Verificar si se debe autoasignar el sponsor
    if rtaSponsor.lower() == "auto":
        rtaSponsor = get_last_registered_alias()
        if not rtaSponsor:
            return JSONResponse(content={"fulfillmentText": "❌ No hay usuarios registrados para asignar como sponsor."})
    else:
        # Verificar si el sponsor existe en la base de datos
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM jugadores WHERE alias = %s", (rtaSponsor,))
        sponsor_exists = cursor.fetchone()
        cursor.close()
        conn.close()

        if not sponsor_exists:
            return JSONResponse(content={"fulfillmentText": f"❌ El usuario {rtaSponsor} no existe. Verifica y vuelve a intentarlo."})

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
        return JSONResponse(content={"fulfillmentText": "❌ Hubo un error al registrar el usuario."})
    finally:
        cursor.close()
        conn.close()

    return JSONResponse(content={"fulfillmentText": f"✅ Usuario {rtaAlias} registrado correctamente con sponsor {rtaSponsor}."})


# ✅ Función para obtener tableros disponibles
def get_open_tableros():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id_tablero, nombre, precio_por_bolita FROM tableros WHERE estado = 'abierto'")
    tableros = cursor.fetchall()
    cursor.close()
    conn.close()
    return tableros

# ✅ Función para obtener el último usuario registrado
def get_last_registered_alias():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT alias FROM jugadores ORDER BY numero_celular DESC LIMIT 1")
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result["alias"] if result else None



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
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    for tablero in tableros:
        ID_tablero_jackpot= tablero['id_tablero']
        
        print(f"entre al ciclo y el id_tablero es: {ID_tablero_jackpot}")
        
        cursor.execute("SELECT premio_ganador FROM jackpots WHERE id_tablero = %s", (ID_tablero_jackpot,))
        jack_premio = cursor.fetchone()
        
        acumulado = jack_premio['premio_ganador'] if jack_premio else 0
        
        print(f"el premio es: {acumulado}")

        acumulado_currency = "${:,.0f}".format(acumulado).replace(',', '.')
        
        precio_bolita = "${:,.0f}".format(tablero['precio_por_bolita']).replace(',', '.')
        botones["inline_keyboard"].append([
            {"text": f"#ID: {tablero['id_tablero']} - 🟢 {precio_bolita}  - 💰 Acum: {acumulado_currency}", "callback_data": f"t4bl3r0s3l|{tablero['id_tablero']}"}
        ])

    cursor.close()
    conn.close()

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

#########

async def handle_seleccionar_tablero(user_id, rtaTableroID):
    if not rtaTableroID:
        return JSONResponse(content={"fulfillmentText": "❌ No se recibió el ID del tablero."})
    
    id_tablero = rtaTableroID.replace("|","")
    print(f"📝 Acción detectada: Tablero Seleccionado {id_tablero}")
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tableros WHERE id_tablero = %s", (id_tablero,))
    tablero = cursor.fetchone()
    
    if not tablero:
        return JSONResponse(content={"fulfillmentText": "❌ Tablero no encontrado."})
    
    cursor.execute("SELECT COUNT(DISTINCT user_id) as inscritos, SUM(cantidad_bolitas) as bolitas_compradas FROM jugadores_tableros WHERE id_tablero = %s", (id_tablero,))
    stats = cursor.fetchone()
    cursor.execute("SELECT * FROM jackpots WHERE id_tablero = %s", (id_tablero,))
    jackpots = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    disponibles = tablero["max_bolitas"] - (stats["bolitas_compradas"] or 0)
    precio_bolita = "${:,.0f}".format(tablero['precio_por_bolita']).replace(',', '.')

    premio_ganador = jackpots['premio_ganador'] if jackpots else 0

    jackpot = "${:,.0f}".format(premio_ganador).replace(',', '.')
    
    return JSONResponse(content={
        "fulfillmentMessages": [{
            "payload": {
                "telegram": {
                    "text": f"📋 Tablero ID: {tablero['id_tablero']}\n\n🟢 Precio/Bolita: {precio_bolita}\n🔹 Mín. por jugador: {tablero['min_bolitas_por_jugador']}\n🔷 Máx. por jugador: {tablero['max_bolitas_por_jugador']}\n🙂 Jugadores inscritos: {stats['inscritos']}\n\n💰 ACUMULADO: {jackpot}",
                    "reply_markup": {"inline_keyboard": [[{"text": "👉 Comprar Bolitas 🚀", "callback_data": f"C0mpr4rB0l1t4s|{id_tablero}"}]]}
                }
            }
        }]
    })

async def handle_comprar_bolitas(user_id, rtaTableroID, rtaCantBolitas):
    if not rtaTableroID:
        return JSONResponse(content={"fulfillmentText": "❌ No se recibió el ID del tablero."})
    
    id_tablero = rtaTableroID.replace("|","")
    cantidad = rtaCantBolitas
    print(f"📝 Acción detectada: Comora {cantidad} en el tablero {id_tablero}")
    
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT saldo FROM jugadores WHERE user_id = %s", (user_id,))
    jugador = cursor.fetchone()
    
    cursor.execute("SELECT * FROM tableros WHERE id_tablero = %s", (id_tablero,))
    tablero = cursor.fetchone()
    
    cursor.execute("SELECT SUM(cantidad_bolitas) as compradas FROM jugadores_tableros WHERE id_tablero = %s", (id_tablero,))
    stats = cursor.fetchone()

    # 🔹 NUEVO: Obtener la cantidad de bolitas compradas por el jugador en este tablero
    cursor.execute("SELECT SUM(cantidad_bolitas) AS compradas_por_jugador FROM jugadores_tableros WHERE user_id = %s AND id_tablero = %s", (user_id, id_tablero))
    jugador_stats = cursor.fetchone()

     # 🔹 NUEVO: Obtener el monto actual del jackpot del tablero
    cursor.execute("SELECT monto_acumulado FROM jackpots WHERE id_tablero = %s", (id_tablero,))
    jackpot = cursor.fetchone()

    cursor.execute("SELECT * FROM configuracion_pagos WHERE id_config = %s", (1,))
    porcentaje_pagos = cursor.fetchone()
    
    
    cursor.close()
    conn.close()
    
    costo_total = int(cantidad) * tablero["precio_por_bolita"]
    ## disponibles = tablero["max_bolitas"] - (stats["compradas"] or 0)
    bolitas_compradas_jugador = jugador_stats["compradas_por_jugador"] or 0
    bolitas_totales_despues_compra = bolitas_compradas_jugador + int(cantidad)
    monto_casa = (jackpot['monto_acumulado'] + costo_total) * porcentaje_pagos["porcentaje_casa"] if jakpot else 0
    monto_sponsor = (jackpot['monto_acumulado'] + costo_total) * porcentaje_pagos["porcentaje_sponsor"] if jakpot else 0
    monto_ganador = (jackpot['monto_acumulado'] + costo_total) * porcentaje_pagos["porcentaje_ganador"] if jakpot else 0
    

    
    if jugador["saldo"] < costo_total:
        return JSONResponse(content={"fulfillmentText": "❌ No tienes saldo suficiente."})
    if cantidad < tablero["min_bolitas_por_jugador"] or cantidad > tablero["max_bolitas_por_jugador"]:
        return JSONResponse(content={"fulfillmentText": "❌ Cantidad de bolitas fuera del rango permitido."})
    '''if cantidad > disponibles:
        return JSONResponse(content={"fulfillmentText": "❌ No hay suficientes bolitas disponibles."})'''
    if bolitas_totales_despues_compra > tablero["max_bolitas_por_jugador"]:
        return JSONResponse(content={"fulfillmentText": f"❌ No puedes comprar más bolitas. Ya tienes {bolitas_compradas_jugador} y el límite es {tablero['max_bolitas_por_jugador']}."})

    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE jugadores SET saldo = saldo - %s WHERE user_id = %s", (costo_total, user_id))
    cursor.execute("INSERT INTO jugadores_tableros (user_id, id_tablero, cantidad_bolitas, monto_pagado) VALUES (%s, %s, %s, %s)", (user_id, id_tablero, cantidad, costo_total))
    if jackpot:
        cursor.execute("UPDATE jackpots SET monto_acumulado = monto_acumulado + %s WHERE id_tablero = %s", (costo_total, id_tablero))
        cursor.execute("UPDATE jackpots SET acum_bolitas = acum_bolitas + %s WHERE id_tablero = %s", (cantidad, id_tablero))
        cursor.execute("UPDATE jackpots SET ganancia_bruta =  %s, premio_sponsor = %s, premio_ganador = %s WHERE id_tablero = %s", (monto_casa, monto_sponsor, monto_ganador, id_tablero))
    
    else:
        cursor.execute("INSERT INTO jackpots (id_tablero, acum_bolitas, monto_acumulado, ganancia_bruta, premio_sponsor, premio_ganador) VALUES (%s, %s, %s, %s, %s, %s)", (id_tablero, cantidad, costo_total, monto_casa, monto_sponsor, monto_ganador))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return JSONResponse(content={"fulfillmentText": "✅ Compra realizada con éxito."})


#########



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

    if action == "actRegistrarUsuario":
        return handle_registrar_usuario(user_id, data)

    if action == "actTableroSelect":
        rtaTableroID = data["queryResult"]["parameters"].get("rtaTableroID")
        return await handle_seleccionar_tablero(user_id, rtaTableroID)
    
    if action == "actComprarBolitas":
        rtaCantBolitas = data["queryResult"]["parameters"].get("rtaCantBolitas")
        rtaTableroID = data["queryResult"]["parameters"].get("rtaTableroID")
        return await handle_comprar_bolitas(user_id, rtaTableroID, rtaCantBolitas)


    return JSONResponse(content={"fulfillmentText": "⚠️ Acción no reconocida."})

# ✅ Función para manejar "MiCuenta"
def handle_mi_cuenta(user_id):
    print("📌 Acción detectada: MiCuenta")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT numero_celular, alias, sponsor, saldo FROM jugadores WHERE user_id = %s", (user_id,))
    usuario = cursor.fetchone()
    cursor.close()
    conn.close()

    if not usuario:
        return JSONResponse(content={"fulfillmentText": "❌ No estás registrado en el sistema."})

    saldo_formateado = "${:,.0f}".format(usuario['saldo']).replace(',', '.')
    
    mensaje = (
        f"Tu cuenta en *Bolas Locas:*\n\n"
        f"👤 *Usuario:* _{usuario['alias']}_\n"
        f"📱 *Número registrado en Nequi:* _{usuario['numero_celular']}_\n"
        f"🤝 *Patrocinador:* _{usuario['sponsor']}_\n\n"
        f"💲 *SALDO:* _{saldo_formateado}_\n\n"
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
                                [{"text": "💲 Recargar saldo", "callback_data": "recargar_saldo"}],
                                [{"text": "🔄 Cambiar número Nequi", "callback_data": "c4mb14r_n3qu1"}],
                                [{"text": "📋 Mis tableros", "callback_data": "M1st4bl4s"}],
                                [{"text": "🔮 Jugar", "callback_data": "1n1c10Ju3g0"}]
                            
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

    
