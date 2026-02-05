"""
Contrôleur Client pour Epic Events CRM

Ce module gère la lecture et création des données clients.
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from epicevents.models import Client, User, RoleEnum
from epicevents.permissions import has_permission


class ClientError(Exception):
    """Exception levée pour les erreurs liées aux clients."""
    pass


def get_all_clients(db: Session, user: User) -> List[Client]:
    """
    Récupère tous les clients.
    
    Args:
        db: Session de base de données
        user: Utilisateur effectuant la requête (doit être authentifié)
        
    Returns:
        Liste des clients
        
    Raises:
        ClientError: Si l'utilisateur n'a pas la permission
    """
    if not has_permission(user, "client.read"):
        raise ClientError("Vous n'avez pas la permission de consulter les clients")
    
    return db.query(Client).all()


def create_client(
    db: Session,
    user: User,
    full_name: str,
    email: str,
    phone: Optional[str] = None,
    company_name: Optional[str] = None
) -> Client:
    """
    Crée un nouveau client.
    
    Args:
        db: Session de base de données
        user: Utilisateur effectuant la création (doit être commercial)
        full_name: Nom complet du client
        email: Email du client
        phone: Numéro de téléphone (optionnel)
        company_name: Nom de l'entreprise (optionnel)
        
    Returns:
        Le client créé
        
    Raises:
        ClientError: Si permission refusée ou données invalides
    """
    # Vérifier les permissions
    if not has_permission(user, "client.create"):
        raise ClientError("Vous n'avez pas la permission de créer des clients")
    
    # Validation des données
    if not full_name or not full_name.strip():
        raise ClientError("Le nom complet est obligatoire")
    
    if not email or not email.strip() or "@" not in email:
        raise ClientError("L'email est invalide")
    
    # Vérifier si l'email existe déjà
    existing = db.query(Client).filter(Client.email == email).first()
    if existing:
        raise ClientError(f"Un client avec l'email '{email}' existe déjà")
    
    client = Client(
        full_name=full_name,
        email=email,
        phone=phone,
        company_name=company_name,
        sales_contact_id=user.id  # Le commercial devient le contact
    )
    
    db.add(client)
    db.commit()
    db.refresh(client)
    
    return client
