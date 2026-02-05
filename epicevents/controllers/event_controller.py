"""
Contrôleur Event pour Epic Events CRM

Ce module gère la lecture des données événements depuis la base.
"""

from typing import List
from sqlalchemy.orm import Session

from epicevents.models import Event, User
from epicevents.permissions import has_permission


class EventError(Exception):
    """Exception levée pour les erreurs liées aux événements."""
    pass


def get_all_events(db: Session, user: User) -> List[Event]:
    """
    Récupère tous les événements.
    
    Args:
        db: Session de base de données
        user: Utilisateur effectuant la requête (doit être authentifié)
        
    Returns:
        Liste des événements
        
    Raises:
        EventError: Si l'utilisateur n'a pas la permission
    """
    if not has_permission(user, "event.read"):
        raise EventError("Vous n'avez pas la permission de consulter les événements")
    
    return db.query(Event).all()
