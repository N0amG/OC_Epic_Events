from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from epicevents.config import DATABASE_URL

# 1. Création du moteur (Engine)
# C'est l'objet qui gère la communication avec la base
engine = create_engine(DATABASE_URL)

# 2. Création de la Session Factory
# C'est l'usine qui va fabriquer des "sessions" (connexions temporaires) pour chaque requête
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. La Base pour les modèles
# Toutes tes futures classes (Client, Contrat...) hériteront de cette variable 'Base'
Base = declarative_base()

# Fonction utilitaire pour récupérer une session (utile pour plus tard)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()