"""
Script d'initialisation de la base de données Epic Events CRM

Ce script :
1. Supprime et recrée toutes les tables (réinitialisation complète)
2. Crée des données de démonstration prédéfinies :
   - 3 utilisateurs (management, sales, support)
   - 3 clients
   - 3 contrats
   - 3 événements

Usage:
    python init_db.py

⚠️ ATTENTION : Ce script SUPPRIME toutes les données existantes !

Note: Assurez-vous que le fichier .env est correctement configuré avant d'exécuter ce script.
"""

from datetime import datetime, timedelta
from decimal import Decimal

from epicevents.database import engine, Base, SessionLocal
from epicevents.models import User, RoleEnum, Client, Contract, Event
from epicevents.controllers.auth_controller import register_user


def reset_database():
    """Supprime et recrée toutes les tables."""
    print("🗑️  Suppression des tables existantes...")
    Base.metadata.drop_all(bind=engine)
    print("✅ Tables supprimées !")
    print("🔨 Création des tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables créées avec succès !")


def create_demo_users():
    """Crée des utilisateurs de démonstration."""
    print("\n👤 Création des utilisateurs de démonstration...")
    
    users_data = [
        {
            "employee_number": "ADMIN001",
            "full_name": "Administrateur",
            "email": "admin@epicevents.com",
            "password": "Admin123!",
            "role": RoleEnum.MANAGEMENT
        },
        {
            "employee_number": "MGT001",
            "full_name": "Marie Manager",
            "email": "marie.manager@epicevents.com",
            "password": "Password123!",
            "role": RoleEnum.MANAGEMENT
        },
        {
            "employee_number": "SAL001",
            "full_name": "Sophie Sales",
            "email": "sophie.sales@epicevents.com",
            "password": "Password123!",
            "role": RoleEnum.SALES
        },
        {
            "employee_number": "SUP001",
            "full_name": "Thomas Support",
            "email": "thomas.support@epicevents.com",
            "password": "Password123!",
            "role": RoleEnum.SUPPORT
        },
        # Utilisateurs pour les tests
        {
            "employee_number": "EMP000",
            "full_name": "Marie Epic",
            "email": "marie@epic.com",
            "password": "password123",
            "role": RoleEnum.MANAGEMENT
        },
        {
            "employee_number": "EMP001",
            "full_name": "Jean Commercial",
            "email": "jean@epic.com",
            "password": "password123",
            "role": RoleEnum.SALES
        },
        {
            "employee_number": "EMP003",
            "full_name": "Paul Support",
            "email": "paul@epic.com",
            "password": "password123",
            "role": RoleEnum.SUPPORT
        }
    ]
    
    created_users = []
    for user_data in users_data:
        user = register_user(**user_data)
        created_users.append(user)
        print(f"   ✓ {user.full_name} ({user.role.value})")
    
    return created_users


def create_demo_clients(db, sales_user):
    """Crée des clients de démonstration."""
    print("\n🏢 Création des clients de démonstration...")
    
    clients_data = [
        {
            "full_name": "Jean Dupont",
            "email": "jean.dupont@entreprise-a.com",
            "phone": "0601020304",
            "company_name": "Entreprise A",
            "sales_contact_id": sales_user.id
        },
        {
            "full_name": "Marie Martin",
            "email": "marie.martin@startup-b.com",
            "phone": "0605060708",
            "company_name": "Startup B",
            "sales_contact_id": sales_user.id
        },
        {
            "full_name": "Pierre Durand",
            "email": "pierre.durand@groupe-c.fr",
            "phone": "0609101112",
            "company_name": "Groupe C",
            "sales_contact_id": sales_user.id
        }
    ]
    
    created_clients = []
    for client_data in clients_data:
        client = Client(**client_data)
        db.add(client)
        db.flush()
        created_clients.append(client)
        print(f"   ✓ {client.full_name} - {client.company_name}")
    
    db.commit()
    return created_clients


def create_demo_contracts(db, clients):
    """Crée des contrats de démonstration."""
    print("\n📄 Création des contrats de démonstration...")
    
    contracts_data = [
        {
            "client_id": clients[0].id,
            "total_amount": Decimal("15000.00"),
            "amount_due": Decimal("5000.00"),
            "is_signed": True
        },
        {
            "client_id": clients[1].id,
            "total_amount": Decimal("25000.00"),
            "amount_due": Decimal("25000.00"),
            "is_signed": True
        },
        {
            "client_id": clients[2].id,
            "total_amount": Decimal("8000.00"),
            "amount_due": Decimal("4000.00"),
            "is_signed": False
        }
    ]
    
    created_contracts = []
    for contract_data in contracts_data:
        contract = Contract(**contract_data)
        db.add(contract)
        db.flush()
        created_contracts.append(contract)
        status = "Signé" if contract.is_signed else "Brouillon"
        print(f"   ✓ Contrat #{contract.id} - {contract.total_amount}€ ({status})")
    
    db.commit()
    return created_contracts


def create_demo_events(db, contracts, support_user):
    """Crée des événements de démonstration."""
    print("\n🎉 Création des événements de démonstration...")
    
    now = datetime.now()
    
    events_data = [
        {
            "contract_id": contracts[0].id,
            "event_date_start": now + timedelta(days=30),
            "event_date_end": now + timedelta(days=30, hours=6),
            "location": "Paris Convention Center",
            "attendees": 150,
            "notes": "Conférence annuelle de l'entreprise",
            "support_contact_id": support_user.id
        },
        {
            "contract_id": contracts[1].id,
            "event_date_start": now + timedelta(days=45),
            "event_date_end": now + timedelta(days=45, hours=4),
            "location": "Lyon Tech Hub",
            "attendees": 80,
            "notes": "Lancement de produit",
            "support_contact_id": support_user.id
        },
        {
            "contract_id": contracts[0].id,
            "event_date_start": now + timedelta(days=60),
            "event_date_end": now + timedelta(days=60, hours=8),
            "location": "Marseille Grand Palais",
            "attendees": 200,
            "notes": "Gala de fin d'année",
            "support_contact_id": support_user.id
        }
    ]
    
    created_events = []
    for event_data in events_data:
        event = Event(**event_data)
        db.add(event)
        db.flush()
        created_events.append(event)
        print(f"   ✓ Événement #{event.id} - {event.location} ({event.attendees} participants)")
    
    db.commit()
    return created_events


def main():
    """Point d'entrée principal du script."""
    print("\n" + "="*70)
    print("  INITIALISATION DE LA BASE DE DONNÉES EPIC EVENTS CRM")
    print("="*70 + "\n")
    
    print("⚠️  ATTENTION : Ce script va SUPPRIMER toutes les données existantes !")
    response = input("Voulez-vous continuer ? (oui/non) : ").lower().strip()
    
    if response not in ["oui", "o", "yes", "y"]:
        print("\n❌ Initialisation annulée.")
        return 0
    
    try:
        # Réinitialiser la base de données
        reset_database()
        
        # Créer une session
        db = SessionLocal()
        
        try:
            # Créer les utilisateurs
            users = create_demo_users()
            manager = users[0]  # Marie Manager
            sales = users[1]     # Sophie Sales
            support = users[2]   # Thomas Support
            
            # Créer les clients (associés au commercial)
            clients = create_demo_clients(db, sales)
            
            # Créer les contrats (pour les clients)
            contracts = create_demo_contracts(db, clients)
            
            # Créer les événements (pour les contrats signés, avec support assigné)
            events = create_demo_events(db, contracts, support)
            
            print("\n" + "="*70)
            print("✨ Initialisation terminée avec succès !")
            print("="*70)
            
            print("\n📊 Données créées :")
            print(f"   • {len(users)} utilisateurs")
            print(f"   • {len(clients)} clients")
            print(f"   • {len(contracts)} contrats")
            print(f"   • {len(events)} événements")
            
            print("\n" + "="*70)
            print("📋 COMPTES DE DÉMONSTRATION")
            print("="*70)
            print("\n🔑 Tous les comptes utilisent le mot de passe : Password123!\n")
            print(f"1. Manager (Gestion)")
            print(f"   Email : marie.manager@epicevents.com")
            print(f"   N° employé : MGT001")
            print()
            print(f"2. Commercial (Sales)")
            print(f"   Email : sophie.sales@epicevents.com")
            print(f"   N° employé : SAL001")
            print()
            print(f"3. Support")
            print(f"   Email : thomas.support@epicevents.com")
            print(f"   N° employé : SUP001")
            print()
            print("="*70)
            print("📋 COMPTES DE TEST (mot de passe: password123)")
            print("="*70)
            print()
            print(f"1. Manager (Tests)")
            print(f"   Email : marie@epic.com")
            print(f"   N° employé : EMP000")
            print()
            print(f"2. Commercial (Tests)")
            print(f"   Email : jean@epic.com")
            print(f"   N° employé : EMP001")
            print()
            print(f"3. Support (Tests)")
            print(f"   Email : paul@epic.com")
            print(f"   N° employé : EMP003")
            print("="*70)
            
            print("\nProchaines étapes :")
            print("  1. Connectez-vous : python epicevents.py login MGT001 Password123!")
            print("  2. Listez les utilisateurs : python epicevents.py user list")
            print("  3. Listez les clients : python epicevents.py client list")
            print("  4. Consultez l'aide : python epicevents.py --help\n")
            
        finally:
            db.close()
        
    except Exception as e:
        print(f"\n❌ Erreur lors de l'initialisation : {e}")
        print("\nVérifiez que :")
        print("  - Le fichier .env est correctement configuré")
        print("  - PostgreSQL est démarré")
        print("  - La base de données existe (voir README.md)")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
