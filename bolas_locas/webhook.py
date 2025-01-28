from fastapi import FastAPI, Request
import mysql.connector
from config import db_config
from fastapi import APIRouter
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse


router = APIRouter()

app = FastAPI()


@router.post("/webhook")
async def handle_dialogflow_webhook(request: Request):
    data = await request.json()
    print("📩 Request de Dialogflow:", data)  # Para depuración
    return JSONResponse(content={"fulfillmentText": "Recibido en webhook"}, status_code=200)



def check_user_registered(user_id):
    """ Verifica si el usuario ya está registrado en la base de datos. """
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT user_id FROM jugadores WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None  # Retorna True si está registrado, False si no

@app.post("/webhook")
async def dialogflow_webhook(request: Request):
    """ Maneja los webhooks de Dialogflow """
    data = await request.json()
    
    # Extraer la intención y la acción de Dialogflow
    intent = data['queryResult']['intent']['displayName']
    action = data['queryResult'].get('action', '')
    user_id = data['originalDetectIntentRequest']['payload']['data']['from']['id']

    # Verificar si se activó la acción actRegistrarUsuario
    if action == "actRegistrarUsuario":
        if check_user_registered(user_id):
            return {"fulfillmentText": "✅ Ya estás registrado en Bolas Locas."}
        else:
            return {"fulfillmentText": "❌ Aún no estás registrado en Bolas Locas."}

    return {"fulfillmentText": "No se reconoce la acción solicitada."}
