"""
Contrôleur Event pour Epic Events CRM

Ce module gère la lecture, création et mise à jour des événements.
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
        user: Utilisateur effectuant la requête (doit être authentifié)
        
    Returns:
        Liste des événements
        
    Raises:
        EventError: Si l'utilisateur n'a pas la permission
    """
    if not has_permission(user, "event.read"):
        raise EventError("Vous n'avez pas la permission de consulter les événements")
    
    return db.query(Event).all()


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
        EventError: Si permission refusée ou données invalides
    """
    # Vérifier les permissions
    if not has_permission(user, "event.create"):
        raise EventError("Vous n'avez pas la permission de créer des événements")
    
    # Validation des données
    if not location or not location.strip():
        raise EventError("Le lieu est obligatoire")
    
    if attendees < 1:
        raise EventError("Le nombre de participants doit être au moins 1")
    
    if event_date_end <= event_date_start:
        raise EventError("La date de fin doit être postérieure à la date de début")
    
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
    
    # Créer l'événement
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
    contract_id: Optional[int] = None,
    support_contact_id: Optional[int] = None,
    event_date_start: Optional[datetime] = None,
    event_date_end: Optional[datetime] = None,
    location: Optional[str] = None,
    attendees: Optional[int] = None,
    notes: Optional[str] = None
) -> Event:
    """
    Met à jour un événement (tous les champs, y compris relationnels).
    
    Args:
        db: Session de base de données
        user: Utilisateur effectuant la mise à jour
        event_id: ID de l'événement
        contract_id: Nouveau contrat (champ relationnel)
        support_contact_id: Nouveau support (champ relationnel)
        event_date_start: Nouvelle date de début
        event_date_end: Nouvelle date de fin
        location: Nouveau lieu
        attendees: Nouveau nombre de participants
        notes: Nouvelles notes
        
    Returns:
        L'événement mis à jour
        
    Raises:
        EventError: Si permission refusée ou données invalides
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
    
    # Validation et application des modifications
    if contract_id is not None:
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            raise EventError(f"Contrat #{contract_id} non trouvé")
        
        if not contract.is_signed:
            raise EventError("Le contrat doit être signé")
        
        event.contract_id = contract_id
    
    if support_contact_id is not None:
        # Seul le management peut modifier le support assigné
        if user.role != RoleEnum.MANAGEMENT:
            raise EventError("Seul le management peut assigner le support")
        
        support_user = db.query(User).filter(User.id == support_contact_id).first()
        if not support_user:
            raise EventError(f"Utilisateur #{support_contact_id} non trouvé")
        
        if support_user.role != RoleEnum.SUPPORT:
            raise EventError(f"{support_user.full_name} n'est pas membre du support")
        
        if not support_user.is_active:
            raise EventError(f"{support_user.full_name} n'est plus actif")
        
        event.support_contact_id = support_contact_id
    
    if event_date_start is not None:
        event.event_date_start = event_date_start
    
    if event_date_end is not None:
        event.event_date_end = event_date_end
    
    # Validation des dates après modification
    if event.event_date_end <= event.event_date_start:
        raise EventError("La date de fin doit être postérieure à la date de début")
    
    if location is not None:
        if not location.strip():
            raise EventError("Le lieu ne peut pas être vide")
        event.location = location
    
    if attendees is not None:
        if attendees < 1:
            raise EventError("Le nombre de participants doit être au moins 1")
        event.attendees = attendees
    
    if notes is not None:
        event.notes = notes
    
    db.commit()
    db.refresh(event)
    
    return event
