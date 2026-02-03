"""
Script de test pour Epic Events CRM
"""
from epicevents.database import engine, Base, SessionLocal
from epicevents.models import User, RoleEnum
from epicevents.controllers.auth_controller import (
    register_user, 
    authenticate_user, 
    get_authenticated_user,
    AuthenticationError
)

# Créer les tables (si elles n'existent pas)
Base.metadata.create_all(bind=engine)

# Créer une session
db = SessionLocal()

# Créer un utilisateur (ou le récupérer s'il existe déjà)
try:
    user = register_user(db, "EMP001", "Jean Dupont", "jean@epic.com", "password123", RoleEnum.SALES)
    print(f"✅ Utilisateur créé : {user.full_name}")
except ValueError as e:
    print(f"ℹ️ Utilisateur existe déjà : {e}")

# Se connecter
user, token = authenticate_user(db, "jean@epic.com", "password123")
print(f"✅ Connecté : {user.full_name}")

# Vérifier la session persistante
try:
    user = get_authenticated_user(db)
    print(f"✅ Session active : {user.full_name}")
except AuthenticationError as e:
    print(f"❌ Erreur session : {e}")

# Fermer la session
db.close()
print("✅ Test terminé avec succès !")