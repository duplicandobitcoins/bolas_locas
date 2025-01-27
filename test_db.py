import mysql.connector
from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

try:
    conn = mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    print("✅ Conexión exitosa a la base de datos")
    conn.close()
except mysql.connector.Error as err:
    print(f"❌ Error al conectar a la base de datos: {err}")
