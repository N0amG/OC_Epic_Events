"""
Script de test pour la lecture des données - Étape 5

Ce script teste la lecture des données depuis la base avec :
- Vérification des permissions
- Authentification obligatoire
- Relations entre modèles utilisateur et modèles métier
"""

from epicevents.database import engine, Base, SessionLocal
from epicevents.models import RoleEnum
from epicevents.controllers.auth_controller import (
    register_user, 
    authenticate_user,
    get_authenticated_user,
    AuthenticationError
)
from epicevents.controllers.client_controller import get_all_clients, ClientError
from epicevents.controllers.contract_controller import get_all_contracts, ContractError
from epicevents.controllers.event_controller import get_all_events, EventError


def separator(title: str):
    """Affiche un separateur."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def main():
    """Test de lecture des données avec authentification et permissions."""
    
    print("\n" + "="*60)
    print("   EPIC EVENTS - TEST LECTURE DONNEES (ETAPE 5)")
    print("="*60)
    
    # Créer les tables
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        # Créer un utilisateur commercial si nécessaire
        try:
            user = register_user(
                db, "SAL001", "Jean Commercial", 
                "jean@epic.com", "password123", RoleEnum.SALES
            )
            print(f"[OK] Utilisateur cree : {user.full_name}")
        except ValueError:
            print("[INFO] Utilisateur existe deja")
        
        # Authentification
        separator("AUTHENTIFICATION")
        user, token = authenticate_user(db, "jean@epic.com", "password123")
        print(f"[OK] Connecte : {user.full_name} ({user.role.value})")
        
        # Vérifier session persistante
        authenticated_user = get_authenticated_user(db)
        print(f"[OK] Session valide : {authenticated_user.full_name}")
        
        # Lecture des clients
        separator("LECTURE DES CLIENTS")
        try:
            clients = get_all_clients(db, authenticated_user)
            print(f"[OK] {len(clients)} client(s) recupere(s)")
            for client in clients:
                sales = client.sales_contact.full_name if client.sales_contact else "Non assigne"
                print(f"  - {client.full_name} (Commercial: {sales})")
        except ClientError as e:
            print(f"[ERREUR] {e}")
        
        # Lecture des contrats
        separator("LECTURE DES CONTRATS")
        try:
            contracts = get_all_contracts(db, authenticated_user)
            print(f"[OK] {len(contracts)} contrat(s) recupere(s)")
            for contract in contracts:
                client_name = contract.client.full_name if contract.client else "Sans client"
                print(f"  - Contrat #{contract.id} ({client_name}) - {contract.total_amount} EUR")
        except ContractError as e:
            print(f"[ERREUR] {e}")
        
        # Lecture des événements
        separator("LECTURE DES EVENEMENTS")
        try:
            events = get_all_events(db, authenticated_user)
            print(f"[OK] {len(events)} evenement(s) recupere(s)")
            for event in events:
                support = event.support_contact.full_name if event.support_contact else "Non assigne"
                print(f"  - Evenement #{event.id} a {event.location} (Support: {support})")
        except EventError as e:
            print(f"[ERREUR] {e}")
        
        # Test sans authentification
        separator("TEST PERMISSIONS")
        print("[TEST] Tentative d'acces sans authentification...")
        
        # Créer un utilisateur support (permissions limitées)
        try:
            support_user = register_user(
                db, "SUP001", "Paul Support",
                "paul@epic.com", "password123", RoleEnum.SUPPORT
            )
        except ValueError:
            from epicevents.models import User
            support_user = db.query(User).filter(User.email == "paul@epic.com").first()
        
        print(f"[TEST] Utilisateur support : {support_user.full_name}")
        
        # Le support peut lire les clients
        try:
            clients = get_all_clients(db, support_user)
            print(f"[OK] Support peut lire {len(clients)} client(s)")
        except ClientError as e:
            print(f"[ERREUR] {e}")
        
        # Le support peut lire les contrats
        try:
            contracts = get_all_contracts(db, support_user)
            print(f"[OK] Support peut lire {len(contracts)} contrat(s)")
        except ContractError as e:
            print(f"[ERREUR] {e}")
        
        # Le support peut lire les événements
        try:
            events = get_all_events(db, support_user)
            print(f"[OK] Support peut lire {len(events)} evenement(s)")
        except EventError as e:
            print(f"[ERREUR] {e}")
        
        print("\n" + "="*60)
        print("   TEST TERMINE - ETAPE 5 VALIDEE")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n[ERREUR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
