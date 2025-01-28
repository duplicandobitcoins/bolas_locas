import mysql.connector
from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

try:
    # Conectar a la base de datos
    connection = mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

    if connection.is_connected():
        print("✅ Conexión exitosa a la base de datos")

        # Ejecutar una consulta de prueba
        cursor = connection.cursor()
        cursor.execute("SHOW TABLES;")  # Lista las tablas en la base de datos
        tables = cursor.fetchall()

        if tables:
            print("📌 Tablas en la base de datos:")
            for table in tables:
                print(f"- {table[0]}")
        else:
            print("⚠️ La base de datos está vacía, no hay tablas.")

        cursor.close()
        connection.close()

except mysql.connector.Error as e:
    print(f"❌ Error conectando a la base de datos: {e}")
