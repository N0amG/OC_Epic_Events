"""
Script de test pour la création et mise à jour - Étape 6

Ce script teste :
- Création de collaborateur
- Modification de collaborateur (y compris département)
- Création de contrat
- Modification de contrat (tous les champs, y compris relationnels)
- Création d'événement
- Modification d'événement (tous les champs, y compris relationnels)
- Validation des données
- Vérification des permissions
"""

from decimal import Decimal
from datetime import datetime, timedelta

from epicevents.database import engine, Base, SessionLocal
from epicevents.models import RoleEnum, User, Client, Contract
from epicevents.controllers.auth_controller import (
    register_user,
    authenticate_user,
    create_user,
    update_user
)
from epicevents.controllers.client_controller import get_all_clients
from epicevents.controllers.contract_controller import (
    create_contract,
    update_contract,
    get_all_contracts,
    ContractError
)
from epicevents.controllers.event_controller import (
    create_event,
    update_event,
    get_all_events,
    EventError
)


def separator(title: str):
    """Affiche un separateur."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def main():
    """Test de création et mise à jour avec validations et permissions."""
    
    print("\n" + "="*60)
    print("   EPIC EVENTS - TEST CREATION/MAJ (ETAPE 6)")
    print("="*60)
    
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        # Créer un utilisateur management
        try:
            mgmt_user = register_user(
                db, "MGT001", "Alice Manager",
                "alice@epic.com", "password123", RoleEnum.MANAGEMENT
            )
            print(f"[OK] Manager cree : {mgmt_user.full_name}")
        except ValueError:
            mgmt_user = db.query(User).filter(
                (User.email == "alice@epic.com") | (User.employee_number == "MGT001")
            ).first()
            if not mgmt_user:
                # Créer avec un ID unique
                import time
                unique_id = f"MGT{int(time.time()) % 10000}"
                mgmt_user = register_user(
                    db, unique_id, "Alice Manager",
                    f"alice.{int(time.time()) % 10000}@epic.com", "password123", 
                    RoleEnum.MANAGEMENT
                )
            print(f"[INFO] Manager existant : {mgmt_user.full_name}")
        
        # Authentification en tant que management
        separator("TEST COLLABORATEURS")
        mgmt_user, _ = authenticate_user(db, mgmt_user.email, "password123")
        print(f"[AUTH] Connecte : {mgmt_user.full_name} ({mgmt_user.role.value})")
        
        # 1. Créer un collaborateur
        try:
            new_user = create_user(
                db, mgmt_user,
                employee_number="TEST001",
                full_name="Bob Test",
                email="bob.test@epic.com",
                password="password123",
                role=RoleEnum.SALES
            )
            print(f"[OK] Collaborateur cree : {new_user.full_name} ({new_user.role.value})")
        except ValueError as e:
            print(f"[INFO] {e}")
            new_user = db.query(User).filter(User.email == "bob.test@epic.com").first()
        
        # 2. Modifier un collaborateur (y compris département)
        try:
            updated_user = update_user(
                db, mgmt_user,
                user_id=new_user.id,
                full_name="Bob Test Modifie",
                role=RoleEnum.SUPPORT  # Changement de département
            )
            print(f"[OK] Collaborateur modifie : {updated_user.full_name}")
            print(f"     Nouveau role : {updated_user.role.value}")
        except ValueError as e:
            print(f"[ERREUR] {e}")
        
        # 3. Test validation : création avec données invalides
        print("\n[TEST] Validation donnees invalides...")
        try:
            create_user(
                db, mgmt_user,
                employee_number="",  # Invalide
                full_name="Test",
                email="test@epic.com",
                password="password123",
                role=RoleEnum.SALES
            )
            print("[ERREUR] Validation non fonctionnelle!")
        except ValueError as e:
            print(f"[OK] Validation OK : {e}")
        
        # 4. Test permission : un commercial ne peut pas créer de collaborateur
        print("\n[TEST] Permission creation collaborateur...")
        sales_user = db.query(User).filter(User.role == RoleEnum.SALES).first()
        if sales_user:
            try:
                create_user(
                    db, sales_user,
                    employee_number="BAD001",
                    full_name="Bad Test",
                    email="bad@epic.com",
                    password="password123",
                    role=RoleEnum.SALES
                )
                print("[ERREUR] Permission non verifiee!")
            except ValueError as e:
                print(f"[OK] Permission OK : {e}")
        
        # Créer un client pour les tests de contrats
        separator("TEST CONTRATS")
        
        # Utiliser un commercial existant
        if not sales_user:
            sales_user = register_user(
                db, "SAL002", "Charlie Sales",
                "charlie@epic.com", "password123", RoleEnum.SALES
            )
        
        # Créer un client
        from epicevents.controllers.client_controller import create_client
        try:
            client = create_client(
                db, sales_user,
                full_name="Test Client Etape6",
                email="client.etape6@test.com"
            )
            print(f"[OK] Client cree : {client.full_name}")
        except Exception:
            client = db.query(Client).filter(
                Client.email == "client.etape6@test.com"
            ).first()
            print(f"[INFO] Client existant : {client.full_name}")
        
        # 5. Créer un contrat
        contract = create_contract(
            db, sales_user,
            client_id=client.id,
            total_amount=Decimal("15000.00")
        )
        print(f"[OK] Contrat cree : #{contract.id} - {contract.total_amount} EUR")
        
        # 6. Modifier un contrat (tous les champs)
        updated_contract = update_contract(
            db, mgmt_user,  # Management peut tout modifier
            contract_id=contract.id,
            total_amount=Decimal("18000.00"),
            amount_due=Decimal("9000.00"),
            is_signed=True
        )
        print(f"[OK] Contrat modifie : #{updated_contract.id}")
        print(f"     Montant : {updated_contract.total_amount} EUR")
        print(f"     Signe : {updated_contract.is_signed}")
        
        # 7. Modifier champ relationnel (client_id)
        # Créer un autre client
        try:
            client2 = create_client(
                db, sales_user,
                full_name="Test Client 2 Etape6",
                email="client2.etape6@test.com"
            )
        except Exception:
            client2 = db.query(Client).filter(
                Client.email == "client2.etape6@test.com"
            ).first()
        
        updated_contract = update_contract(
            db, sales_user,
            contract_id=contract.id,
            client_id=client2.id  # Modification champ relationnel
        )
        print(f"[OK] Contrat relie a nouveau client : {updated_contract.client.full_name}")
        
        # 8. Test validation contrat
        print("\n[TEST] Validation contrat...")
        try:
            create_contract(
                db, sales_user,
                client_id=client.id,
                total_amount=Decimal("-1000")  # Invalide
            )
            print("[ERREUR] Validation non fonctionnelle!")
        except ContractError as e:
            print(f"[OK] Validation OK : {e}")
        
        # Tests événements
        separator("TEST EVENEMENTS")
        
        # 9. Créer un événement
        event = create_event(
            db, sales_user,
            contract_id=updated_contract.id,
            event_date_start=datetime.now() + timedelta(days=15),
            event_date_end=datetime.now() + timedelta(days=15, hours=6),
            location="Lyon - Centre de Congres",
            attendees=200,
            notes="Evenement test etape 6"
        )
        print(f"[OK] Evenement cree : #{event.id} a {event.location}")
        
        # 10. Modifier un événement (tous les champs)
        updated_event = update_event(
            db, mgmt_user,  # Management peut tout modifier
            event_id=event.id,
            location="Lyon - Palais des Congres",
            attendees=250,
            notes="Evenement test modifie"
        )
        print(f"[OK] Evenement modifie : #{updated_event.id}")
        print(f"     Lieu : {updated_event.location}")
        print(f"     Participants : {updated_event.attendees}")
        
        # 11. Modifier champ relationnel (support_contact_id)
        support_user = db.query(User).filter(User.role == RoleEnum.SUPPORT).first()
        if support_user:
            updated_event = update_event(
                db, mgmt_user,
                event_id=event.id,
                support_contact_id=support_user.id  # Modification champ relationnel
            )
            print(f"[OK] Support assigne : {updated_event.support_contact.full_name}")
        
        # 12. Test validation événement
        print("\n[TEST] Validation evenement...")
        try:
            create_event(
                db, sales_user,
                contract_id=updated_contract.id,
                event_date_start=datetime.now() + timedelta(days=10),
                event_date_end=datetime.now() + timedelta(days=9),  # Invalide
                location="Test",
                attendees=10
            )
            print("[ERREUR] Validation non fonctionnelle!")
        except EventError as e:
            print(f"[OK] Validation OK : {e}")
        
        # 13. Test permission événement
        print("\n[TEST] Permission modification support...")
        if support_user:
            try:
                update_event(
                    db, sales_user,  # Commercial ne peut pas assigner support
                    event_id=event.id,
                    support_contact_id=support_user.id
                )
                print("[ERREUR] Permission non verifiee!")
            except EventError as e:
                print(f"[OK] Permission OK : {e}")
        
        # Résumé
        separator("RESUME")
        total_users = db.query(User).count()
        total_contracts = db.query(Contract).count()
        total_events = db.query(Contract).count()
        
        print(f"  Collaborateurs : {total_users}")
        print(f"  Contrats       : {total_contracts}")
        print(f"  Evenements     : {total_events}")
        
        print("\n" + "="*60)
        print("   TEST TERMINE - ETAPE 6 VALIDEE")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n[ERREUR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
