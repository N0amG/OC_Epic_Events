"""
Contrôleur Event pour Epic Events CRM

Ce module gère toutes les opérations CRUD sur les événements.
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from epicevents.models import Event, Contract, User, RoleEnum
from epicevents.permissions import has_permission


class EventError(Exception):
    """Exception levée pour les erreurs liées aux événements."""
    pass


def get_all_events(db: Session, user: User) -> List[Event]:
    """
    Récupère tous les événements.
    
    Args:
        db: Session de base de données
        user: Utilisateur effectuant la requête
        
    Returns:
        Liste des événements
        
    Raises:
        EventError: Si l'utilisateur n'a pas la permission
    """
    if not has_permission(user, "event.read"):
        raise EventError("Vous n'avez pas la permission de consulter les événements")
    
    return db.query(Event).all()


def get_event_by_id(db: Session, user: User, event_id: int) -> Event:
    """
    Récupère un événement par son ID.
    
    Args:
        db: Session de base de données
        user: Utilisateur effectuant la requête
        event_id: ID de l'événement
        
    Returns:
        L'événement trouvé
        
    Raises:
        EventError: Si l'événement n'existe pas ou permission refusée
    """
    if not has_permission(user, "event.read"):
        raise EventError("Vous n'avez pas la permission de consulter les événements")
    
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise EventError(f"Événement #{event_id} non trouvé")
    
    return event


def get_my_events(db: Session, user: User) -> List[Event]:
    """
    Récupère les événements assignés au support connecté.
    
    Args:
        db: Session de base de données
        user: Utilisateur support
        
    Returns:
        Liste des événements assignés
    """
    if user.role != RoleEnum.SUPPORT:
        raise EventError("Seul le support a des événements assignés")
    
    return db.query(Event).filter(Event.support_contact_id == user.id).all()


def get_unassigned_events(db: Session, user: User) -> List[Event]:
    """
    Récupère les événements sans support assigné.
    
    Args:
        db: Session de base de données
        user: Utilisateur effectuant la requête
        
    Returns:
        Liste des événements non assignés
    """
    if not has_permission(user, "event.read"):
        raise EventError("Vous n'avez pas la permission de consulter les événements")
    
    return db.query(Event).filter(Event.support_contact_id == None).all()


def create_event(
    db: Session,
    user: User,
    contract_id: int,
    event_date_start: datetime,
    event_date_end: datetime,
    location: str,
    attendees: int,
    notes: Optional[str] = None
) -> Event:
    """
    Crée un nouvel événement.
    
    Args:
        db: Session de base de données
        user: Utilisateur effectuant la création
        contract_id: ID du contrat associé
        event_date_start: Date/heure de début
        event_date_end: Date/heure de fin
        location: Lieu de l'événement
        attendees: Nombre de participants
        notes: Notes supplémentaires (optionnel)
        
    Returns:
        L'événement créé
        
    Raises:
        EventError: Si permission refusée ou contrat non trouvé/non signé
    """
    if not has_permission(user, "event.create"):
        raise EventError("Vous n'avez pas la permission de créer des événements")
    
    # Vérifier que le contrat existe
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise EventError(f"Contrat #{contract_id} non trouvé")
    
    # Vérifier que le contrat est signé
    if not contract.is_signed:
        raise EventError("Impossible de créer un événement pour un contrat non signé")
    
    # Un commercial ne peut créer un événement que pour ses propres clients
    if user.role == RoleEnum.SALES:
        if contract.client and contract.client.sales_contact_id != user.id:
            raise EventError("Vous ne pouvez créer des événements que pour vos clients")
    
    # Validation des dates
    if event_date_end < event_date_start:
        raise EventError("La date de fin doit être postérieure à la date de début")
    
    if attendees < 1:
        raise EventError("Le nombre de participants doit être au moins 1")
    
    event = Event(
        contract_id=contract_id,
        event_date_start=event_date_start,
        event_date_end=event_date_end,
        location=location,
        attendees=attendees,
        notes=notes
    )
    
    db.add(event)
    db.commit()
    db.refresh(event)
    
    return event


def update_event(
    db: Session,
    user: User,
    event_id: int,
    event_date_start: Optional[datetime] = None,
    event_date_end: Optional[datetime] = None,
    location: Optional[str] = None,
    attendees: Optional[int] = None,
    notes: Optional[str] = None
) -> Event:
    """
    Met à jour un événement.
    
    Args:
        db: Session de base de données
        user: Utilisateur effectuant la mise à jour
        event_id: ID de l'événement
        event_date_start: Nouvelle date de début (optionnel)
        event_date_end: Nouvelle date de fin (optionnel)
        location: Nouveau lieu (optionnel)
        attendees: Nouveau nombre de participants (optionnel)
        notes: Nouvelles notes (optionnel)
        
    Returns:
        L'événement mis à jour
        
    Raises:
        EventError: Si permission refusée ou événement non trouvé
    """
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise EventError(f"Événement #{event_id} non trouvé")
    
    # Vérifier les permissions
    can_update = False
    if has_permission(user, "event.update"):
        can_update = True
    elif has_permission(user, "event.update_own"):
        if event.support_contact_id == user.id:
            can_update = True
    
    if not can_update:
        raise EventError("Vous n'avez pas la permission de modifier cet événement")
    
    # Appliquer les modifications
    if event_date_start is not None:
        event.event_date_start = event_date_start
    if event_date_end is not None:
        event.event_date_end = event_date_end
    if location is not None:
        event.location = location
    if attendees is not None:
        if attendees < 1:
            raise EventError("Le nombre de participants doit être au moins 1")
        event.attendees = attendees
    if notes is not None:
        event.notes = notes
    
    # Validation des dates après modification
    if event.event_date_end < event.event_date_start:
        raise EventError("La date de fin doit être postérieure à la date de début")
    
    db.commit()
    db.refresh(event)
    
    return event


def assign_support(
    db: Session,
    user: User,
    event_id: int,
    support_id: int
) -> Event:
    """
    Assigne un membre du support à un événement (management seulement).
    
    Args:
        db: Session de base de données
        user: Utilisateur effectuant l'assignation
        event_id: ID de l'événement
        support_id: ID de l'utilisateur support
        
    Returns:
        L'événement mis à jour
        
    Raises:
        EventError: Si permission refusée ou utilisateur non support
    """
    if user.role != RoleEnum.MANAGEMENT:
        raise EventError("Seul le management peut assigner le support")
    
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise EventError(f"Événement #{event_id} non trouvé")
    
    # Vérifier que l'utilisateur cible est bien du support
    support_user = db.query(User).filter(User.id == support_id).first()
    if not support_user:
        raise EventError(f"Utilisateur #{support_id} non trouvé")
    
    if support_user.role != RoleEnum.SUPPORT:
        raise EventError(f"{support_user.full_name} n'est pas membre du support")
    
    if not support_user.is_active:
        raise EventError(f"{support_user.full_name} n'est plus actif")
    
    event.support_contact_id = support_id
    
    db.commit()
    db.refresh(event)
    
    return event
