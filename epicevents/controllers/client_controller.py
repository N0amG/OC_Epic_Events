"""
Contrôleur Client pour Epic Events CRM

Ce module gère la lecture des données clients depuis la base.
"""

from typing import List
from sqlalchemy.orm import Session

from epicevents.models import Client, User
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
