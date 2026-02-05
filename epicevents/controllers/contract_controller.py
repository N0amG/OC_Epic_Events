"""
Contrôleur Contract pour Epic Events CRM

Ce module gère la lecture des données contrats depuis la base.
"""

from typing import List
from sqlalchemy.orm import Session

from epicevents.models import Contract, User
from epicevents.permissions import has_permission


class ContractError(Exception):
    """Exception levée pour les erreurs liées aux contrats."""
    pass


def get_all_contracts(db: Session, user: User) -> List[Contract]:
    """
    Récupère tous les contrats.
    
    Args:
        db: Session de base de données
        user: Utilisateur effectuant la requête (doit être authentifié)
        
    Returns:
        Liste des contrats
        
    Raises:
        ContractError: Si l'utilisateur n'a pas la permission
    """
    if not has_permission(user, "contract.read"):
        raise ContractError("Vous n'avez pas la permission de consulter les contrats")
    
    return db.query(Contract).all()
