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
