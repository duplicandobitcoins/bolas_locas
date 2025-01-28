import os

# Configuración de la base de datos de Railway
DB_HOST = os.getenv("DB_HOST", "mysql.railway.internal")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "gipLtWlfZfkaopbYuWSfKmbnxxwQuhLZ")
DB_NAME = os.getenv("DB_NAME", "railway")
