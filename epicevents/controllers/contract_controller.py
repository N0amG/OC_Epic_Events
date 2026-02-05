"""
Contrôleur Contract pour Epic Events CRM

Ce module gère la lecture, création et mise à jour des contrats.
"""

from typing import List, Optional
from decimal import Decimal
from sqlalchemy.orm import Session

from epicevents.models import Contract, Client, User, RoleEnum
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


def create_contract(
    db: Session,
    user: User,
    client_id: int,
    total_amount: Decimal,
    amount_due: Optional[Decimal] = None
) -> Contract:
    """
    Crée un nouveau contrat.
    
    Args:
        db: Session de base de données
        user: Utilisateur effectuant la création
        client_id: ID du client
        total_amount: Montant total du contrat
        amount_due: Montant restant dû (par défaut = total_amount)
        
    Returns:
        Le contrat créé
        
    Raises:
        ContractError: Si permission refusée ou données invalides
    """
    # Vérifier les permissions
    if not has_permission(user, "contract.create"):
        raise ContractError("Vous n'avez pas la permission de créer des contrats")
    
    # Validation des données
    if total_amount <= 0:
        raise ContractError("Le montant total doit être positif")
    
    # Vérifier que le client existe
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise ContractError(f"Client #{client_id} non trouvé")
    
    # Un commercial ne peut créer un contrat que pour ses propres clients
    if user.role == RoleEnum.SALES and client.sales_contact_id != user.id:
        raise ContractError("Vous ne pouvez créer des contrats que pour vos clients")
    
    if amount_due is None:
        amount_due = total_amount
    
    if amount_due < 0 or amount_due > total_amount:
        raise ContractError("Le montant dû doit être entre 0 et le montant total")
    
    # Créer le contrat
    contract = Contract(
        client_id=client_id,
        total_amount=total_amount,
        amount_due=amount_due,
        is_signed=False
    )
    
    db.add(contract)
    db.commit()
    db.refresh(contract)
    
    return contract


def update_contract(
    db: Session,
    user: User,
    contract_id: int,
    client_id: Optional[int] = None,
    total_amount: Optional[Decimal] = None,
    amount_due: Optional[Decimal] = None,
    is_signed: Optional[bool] = None
) -> Contract:
    """
    Met à jour un contrat (tous les champs, y compris relationnels).
    
    Args:
        db: Session de base de données
        user: Utilisateur effectuant la mise à jour
        contract_id: ID du contrat
        client_id: Nouveau client (champ relationnel)
        total_amount: Nouveau montant total
        amount_due: Nouveau montant dû
        is_signed: Nouveau statut de signature
        
    Returns:
        Le contrat mis à jour
        
    Raises:
        ContractError: Si permission refusée ou données invalides
    """
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise ContractError(f"Contrat #{contract_id} non trouvé")
    
    # Vérifier les permissions
    can_update = False
    if has_permission(user, "contract.update"):
        can_update = True
    elif has_permission(user, "contract.update_own"):
        # Vérifier que c'est un contrat de son client
        if contract.client and contract.client.sales_contact_id == user.id:
            can_update = True
    
    if not can_update:
        raise ContractError("Vous n'avez pas la permission de modifier ce contrat")
    
    # Validation et application des modifications
    if client_id is not None:
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise ContractError(f"Client #{client_id} non trouvé")
        
        # Si commercial, vérifier qu'il peut lier ce client
        if user.role == RoleEnum.SALES and client.sales_contact_id != user.id:
            raise ContractError("Vous ne pouvez lier que vos propres clients")
        
        contract.client_id = client_id
    
    if total_amount is not None:
        if total_amount <= 0:
            raise ContractError("Le montant total doit être positif")
        contract.total_amount = total_amount
    
    if amount_due is not None:
        if amount_due < 0:
            raise ContractError("Le montant dû ne peut pas être négatif")
        if amount_due > contract.total_amount:
            raise ContractError("Le montant dû ne peut pas dépasser le montant total")
        contract.amount_due = amount_due
    
    if is_signed is not None:
        contract.is_signed = is_signed
    
    db.commit()
    db.refresh(contract)
    
    return contract
