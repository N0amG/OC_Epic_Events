"""
Contrôleur Event pour Epic Events CRM

Ce module gère la lecture, création et mise à jour des événements.
"""

from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session, joinedload

from epicevents.models import Event, Contract, User, RoleEnum
from epicevents.permissions import has_permission
from epicevents.database import get_db
from epicevents.controllers.auth_controller import get_authenticated_user


class EventError(Exception):
    """Exception levée pour les erreurs liées aux événements."""
    pass


def get_all_events() -> List[dict]:
    """
    Récupère tous les événements sous forme de dicts prêts à l'affichage.
    
    Returns:
        Liste de dicts événements
        
    Raises:
        AuthenticationError: Si non authentifié
        EventError: Si l'utilisateur n'a pas la permission
    """
    with get_db() as db:
        user = get_authenticated_user(db)
        if not has_permission(user, "event.read"):
            raise EventError("Vous n'avez pas la permission de consulter les événements")

        events = db.query(Event).options(
            joinedload(Event.contract).joinedload(Contract.client),
            joinedload(Event.support_contact)
        ).all()
        return [
            {
                "id": e.id,
                "client_name": (
                    e.contract.client.full_name
                    if e.contract and e.contract.client
                    else "N/A"
                ),
                "location": (e.location or "N/A")[:18],
                "start": e.event_date_start.strftime("%Y-%m-%d %H:%M"),
                "end": e.event_date_end.strftime("%Y-%m-%d %H:%M"),
                "attendees": e.attendees,
                "support": (
                    e.support_contact.full_name if e.support_contact else "Non assigné"
                ),
            }
            for e in events
        ]


def create_event(
    contract_id: int,
    event_date_start: str,
    event_date_end: str,
    location: str,
    attendees: int,
    notes: Optional[str] = None
) -> Event:
    """
    Crée un nouvel événement.
    
    Args:
        contract_id: ID du contrat associé
        event_date_start: Date/heure de début (format: YYYY-MM-DD HH:MM)
        event_date_end: Date/heure de fin (format: YYYY-MM-DD HH:MM)
        location: Lieu de l'événement
        attendees: Nombre de participants
        notes: Notes supplémentaires (optionnel)
        
    Returns:
        L'événement créé
        
    Raises:
        AuthenticationError: Si non authentifié
        EventError: Si permission refusée ou données invalides
    """
    with get_db() as db:
        user = get_authenticated_user(db)
        
        # Vérifier les permissions
        if not has_permission(user, "event.create"):
            raise EventError("Vous n'avez pas la permission de créer des événements")
        
        # Convertir les dates string en datetime
        try:
            start = datetime.strptime(event_date_start, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            end = datetime.strptime(event_date_end, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        except ValueError as e:
            raise EventError(f"Format de date invalide: {e}")
        
        # Validation des données
        if not location or not location.strip():
            raise EventError("Le lieu est obligatoire")
        
        if attendees < 1:
            raise EventError("Le nombre de participants doit être au moins 1")
        
        if end <= start:
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
            event_date_start=start,
            event_date_end=end,
            location=location,
            attendees=attendees,
            notes=notes
        )
        
        db.add(event)
        db.commit()
        db.refresh(event)
        
        return event


def update_event(
    event_id: int,
    contract_id: Optional[int] = None,
    support_contact_id: Optional[int] = None,
    event_date_start: Optional[str] = None,
    event_date_end: Optional[str] = None,
    location: Optional[str] = None,
    attendees: Optional[int] = None,
    notes: Optional[str] = None
) -> Event:
    """
    Met à jour un événement (tous les champs, y compris relationnels).
    
    Args:
        event_id: ID de l'événement
        contract_id: Nouveau contrat (champ relationnel)
        support_contact_id: Nouveau support (champ relationnel)
        event_date_start: Nouvelle date de début (format: YYYY-MM-DD HH:MM)
        event_date_end: Nouvelle date de fin (format: YYYY-MM-DD HH:MM)
        location: Nouveau lieu
        attendees: Nouveau nombre de participants
        notes: Nouvelles notes
        
    Returns:
        L'événement mis à jour
        
    Raises:
        AuthenticationError: Si non authentifié
        EventError: Si permission refusée ou données invalides
    """
    with get_db() as db:
        user = get_authenticated_user(db)
        
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
            try:
                event.event_date_start = datetime.strptime(event_date_start, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            except ValueError as e:
                raise EventError(f"Format de date de début invalide: {e}")
        
        if event_date_end is not None:
            try:
                event.event_date_end = datetime.strptime(event_date_end, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            except ValueError as e:
                raise EventError(f"Format de date de fin invalide: {e}")
        
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


def delete_event(event_id: int) -> bool:
    """
    Supprime un événement.
    
    Args:
        event_id: ID de l'événement à supprimer
        
    Returns:
        True si la suppression a réussi
        
    Raises:
        AuthenticationError: Si non authentifié
        EventError: Si permission refusée ou événement non trouvé
    """
    with get_db() as db:
        user = get_authenticated_user(db)
        
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise EventError(f"Événement #{event_id} non trouvé")
        
        # Vérifier les permissions
        can_delete = False
        if has_permission(user, "event.delete"):
            # Management peut supprimer tous les événements
            can_delete = True
        elif has_permission(user, "event.delete_own"):
            # Support peut supprimer ses événements assignés
            if user.role == RoleEnum.SUPPORT and event.support_contact_id == user.id:
                can_delete = True
            # Commercial peut supprimer les événements de ses contrats
            elif user.role == RoleEnum.SALES:
                if event.contract and event.contract.client and event.contract.client.sales_contact_id == user.id:
                    can_delete = True
        
        if not can_delete:
            raise EventError("Vous n'avez pas la permission de supprimer cet événement")
        
        db.delete(event)
        db.commit()
        
        return True
