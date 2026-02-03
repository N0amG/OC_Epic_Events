"""
Gestion des permissions pour Epic Events CRM

Ce module définit les autorisations basées sur les rôles :
- MANAGEMENT : Gestion des collaborateurs, supervision globale
- SALES : Gestion des clients et contrats
- SUPPORT : Gestion des événements assignés

Différence Authentification vs Autorisation :
- Authentification : "Qui êtes-vous ?" → Vérification de l'identité (login)
- Autorisation : "Que pouvez-vous faire ?" → Vérification des permissions
"""

from functools import wraps
from typing import Callable, List

from epicevents.models import User, RoleEnum, Client, Contract, Event


# ============================================================
# DÉFINITION DES PERMISSIONS PAR RÔLE
# ============================================================

PERMISSIONS = {
    RoleEnum.MANAGEMENT: [
        # Gestion des collaborateurs
        "user.create",
        "user.read",
        "user.update",
        "user.delete",
        # Lecture globale
        "client.read",
        "contract.read",
        "contract.update",  # Peut modifier tous les contrats
        "event.read",
        "event.update",     # Peut assigner le support aux événements
    ],
    RoleEnum.SALES: [
        # Gestion des clients
        "client.create",
        "client.read",
        "client.update_own",  # Uniquement ses propres clients
        # Gestion des contrats
        "contract.create",    # Pour ses propres clients
        "contract.read",
        "contract.update_own",  # Uniquement les contrats de ses clients
        # Lecture des événements
        "event.create",       # Pour les contrats signés de ses clients
        "event.read",
    ],
    RoleEnum.SUPPORT: [
        # Lecture seule clients/contrats
        "client.read",
        "contract.read",
        # Gestion des événements assignés
        "event.read",
        "event.update_own",   # Uniquement ses événements assignés
    ],
}


def get_user_permissions(user: User) -> List[str]:
    """
    Retourne la liste des permissions d'un utilisateur.
    
    Args:
        user: L'utilisateur
        
    Returns:
        Liste des permissions
    """
    return PERMISSIONS.get(user.role, [])


def has_permission(user: User, permission: str) -> bool:
    """
    Vérifie si un utilisateur a une permission spécifique.
    
    Args:
        user: L'utilisateur
        permission: La permission à vérifier (ex: "client.create")
        
    Returns:
        True si l'utilisateur a la permission
    """
    user_permissions = get_user_permissions(user)
    return permission in user_permissions


def require_permission(permission: str):
    """
    Décorateur pour protéger une fonction avec une permission.
    
    Usage:
        @require_permission("client.create")
        def create_client(user, ...):
            ...
    
    Args:
        permission: La permission requise
        
    Raises:
        PermissionError: Si l'utilisateur n'a pas la permission
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(user: User, *args, **kwargs):
            if not has_permission(user, permission):
                raise PermissionError(
                    f"Permission refusée : '{permission}' requise. "
                    f"Votre rôle ({user.role.value}) ne permet pas cette action."
                )
            return func(user, *args, **kwargs)
        return wrapper
    return decorator


def require_role(*roles: RoleEnum):
    """
    Décorateur pour restreindre l'accès à certains rôles.
    
    Usage:
        @require_role(RoleEnum.MANAGEMENT, RoleEnum.SALES)
        def some_function(user, ...):
            ...
    
    Args:
        *roles: Les rôles autorisés
        
    Raises:
        PermissionError: Si l'utilisateur n'a pas le bon rôle
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(user: User, *args, **kwargs):
            if user.role not in roles:
                allowed = ", ".join([r.value for r in roles])
                raise PermissionError(
                    f"Accès refusé. Rôles autorisés : {allowed}. "
                    f"Votre rôle : {user.role.value}"
                )
            return func(user, *args, **kwargs)
        return wrapper
    return decorator


# ============================================================
# VÉRIFICATIONS SPÉCIFIQUES (Ownership)
# ============================================================

def is_client_owner(user: User, client: Client) -> bool:
    """
    Vérifie si l'utilisateur est le commercial du client.
    
    Args:
        user: L'utilisateur (commercial)
        client: Le client
        
    Returns:
        True si l'utilisateur est le commercial du client
    """
    return client.sales_contact_id == user.id


def is_event_support(user: User, event: Event) -> bool:
    """
    Vérifie si l'utilisateur est le support assigné à l'événement.
    
    Args:
        user: L'utilisateur (support)
        event: L'événement
        
    Returns:
        True si l'utilisateur est assigné à l'événement
    """
    return event.support_contact_id == user.id


def can_modify_client(user: User, client: Client) -> bool:
    """
    Vérifie si l'utilisateur peut modifier un client.
    
    - MANAGEMENT : peut lire mais pas modifier directement
    - SALES : peut modifier uniquement ses clients
    - SUPPORT : lecture seule
    
    Args:
        user: L'utilisateur
        client: Le client
        
    Returns:
        True si l'utilisateur peut modifier le client
    """
    if user.role == RoleEnum.SALES:
        return is_client_owner(user, client)
    return False


def can_modify_contract(user: User, contract: Contract) -> bool:
    """
    Vérifie si l'utilisateur peut modifier un contrat.
    
    - MANAGEMENT : peut modifier tous les contrats
    - SALES : peut modifier les contrats de ses clients
    - SUPPORT : lecture seule
    
    Args:
        user: L'utilisateur
        contract: Le contrat
        
    Returns:
        True si l'utilisateur peut modifier le contrat
    """
    if user.role == RoleEnum.MANAGEMENT:
        return True
    if user.role == RoleEnum.SALES:
        return contract.client.sales_contact_id == user.id
    return False


def can_modify_event(user: User, event: Event) -> bool:
    """
    Vérifie si l'utilisateur peut modifier un événement.
    
    - MANAGEMENT : peut assigner le support
    - SALES : lecture seule
    - SUPPORT : peut modifier ses événements assignés
    
    Args:
        user: L'utilisateur
        event: L'événement
        
    Returns:
        True si l'utilisateur peut modifier l'événement
    """
    if user.role == RoleEnum.MANAGEMENT:
        return True
    if user.role == RoleEnum.SUPPORT:
        return is_event_support(user, event)
    return False
