import os
from dotenv import load_dotenv

# Charge les variables depuis le fichier .env qui est à la racine
load_dotenv()

# On récupère les variables
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")

# On construit l'URL de connexion à la base de données
DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"