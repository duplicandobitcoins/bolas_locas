import os

DB_HOST = os.getenv("MYSQLHOST", "mysql.railway.internal")
DB_PORT = os.getenv("MYSQLPORT", "3306")
DB_USER = os.getenv("MYSQLUSER", "root")
DB_PASSWORD = os.getenv("MYSQLPASSWORD", "tu_password_aqui")
DB_NAME = os.getenv("MYSQLDATABASE", "railway")
