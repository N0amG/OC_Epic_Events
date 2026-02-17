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
# Configuration Sentry
SENTRY_DSN = os.getenv("SENTRY_DSN")
# Nettoyer SENTRY_DSN : retirer les commentaires et espaces
if SENTRY_DSN:
    SENTRY_DSN = SENTRY_DSN.strip()
    # Si la valeur commence par #, la considérer comme vide
    if SENTRY_DSN.startswith('#'):
        SENTRY_DSN = None
    # Si la valeur est vide après nettoyage, la mettre à None
    if not SENTRY_DSN:
        SENTRY_DSN = None

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
