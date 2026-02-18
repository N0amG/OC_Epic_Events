"""
Contrôleur Client pour Epic Events CRM

Ce module gère la lecture et création des données clients.
"""

from typing import List, Optional
from sqlalchemy.orm import Session, joinedload

from epicevents.models import Client, User, RoleEnum
from epicevents.permissions import has_permission
from epicevents.database import get_db
from epicevents.controllers.auth_controller import get_authenticated_user


class ClientError(Exception):
    """Exception levée pour les erreurs liées aux clients."""

    pass


def get_all_clients() -> List[dict]:
    """
    Récupère tous les clients sous forme de dicts prêts à l'affichage.

    Returns:
        Liste de dicts clients

    Raises:
        AuthenticationError: Si non authentifié
        ClientError: Si l'utilisateur n'a pas la permission
    """
    with get_db() as db:
        user = get_authenticated_user(db)
        if not has_permission(user, "client.read"):
            raise ClientError("Vous n'avez pas la permission de consulter les clients")

        clients = db.query(Client).options(joinedload(Client.sales_contact)).all()
        return [
            {
                "id": c.id,
                "full_name": c.full_name,
                "email": c.email,
                "phone": c.phone or "N/A",
                "company_name": c.company_name or "N/A",
                "sales_contact": c.sales_contact.full_name if c.sales_contact else "N/A",
            }
            for c in clients
        ]


def create_client(
    full_name: str,
    email: str,
    phone: Optional[str] = None,
    company_name: Optional[str] = None,
) -> Client:
    """
    Crée un nouveau client.

    Args:
        full_name: Nom complet du client
        email: Email du client
        phone: Numéro de téléphone (optionnel)
        company_name: Nom de l'entreprise (optionnel)

    Returns:
        Le client créé

    Raises:
        AuthenticationError: Si non authentifié
        ClientError: Si permission refusée ou données invalides
    """
    with get_db() as db:
        user = get_authenticated_user(db)
        
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
            sales_contact_id=user.id,  # Le commercial devient le contact
        )

        db.add(client)
        db.commit()
        db.refresh(client)

        return client


def delete_client(client_id: int) -> bool:
    """
    Supprime un client.
    
    Args:
        client_id: ID du client à supprimer
        
    Returns:
        True si la suppression a réussi
        
    Raises:
        AuthenticationError: Si non authentifié
        ClientError: Si permission refusée ou client non trouvé
    """
    with get_db() as db:
        user = get_authenticated_user(db)
        
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise ClientError(f"Client #{client_id} non trouvé")
        
        # Vérifier les permissions
        can_delete = False
        if has_permission(user, "client.delete"):
            # Management peut supprimer tous les clients
            can_delete = True
        elif has_permission(user, "client.delete_own"):
            # Commercial peut supprimer uniquement ses propres clients
            if client.sales_contact_id == user.id:
                can_delete = True
        
        if not can_delete:
            raise ClientError("Vous n'avez pas la permission de supprimer ce client")
        
        db.delete(client)
        db.commit()
        
        return True
