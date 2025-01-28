from fastapi import FastAPI
import mysql.connector
from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

app = FastAPI()

@app.get("/test-db")
def test_db():
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("SHOW TABLES;")
            tables = cursor.fetchall()
            cursor.close()
            connection.close()
            return {"status": "success", "tables": [table[0] for table in tables]}
    except Exception as e:
        return {"status": "error", "message": str(e)}
