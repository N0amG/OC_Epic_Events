"""
Contrôleur Contract pour Epic Events CRM

Ce module gère toutes les opérations CRUD sur les contrats.
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
        user: Utilisateur effectuant la requête
        
    Returns:
        Liste des contrats
        
    Raises:
        ContractError: Si l'utilisateur n'a pas la permission
    """
    if not has_permission(user, "contract.read"):
        raise ContractError("Vous n'avez pas la permission de consulter les contrats")
    
    return db.query(Contract).all()


def get_contract_by_id(db: Session, user: User, contract_id: int) -> Contract:
    """
    Récupère un contrat par son ID.
    
    Args:
        db: Session de base de données
        user: Utilisateur effectuant la requête
        contract_id: ID du contrat
        
    Returns:
        Le contrat trouvé
        
    Raises:
        ContractError: Si le contrat n'existe pas ou permission refusée
    """
    if not has_permission(user, "contract.read"):
        raise ContractError("Vous n'avez pas la permission de consulter les contrats")
    
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise ContractError(f"Contrat #{contract_id} non trouvé")
    
    return contract


def get_unsigned_contracts(db: Session, user: User) -> List[Contract]:
    """
    Récupère les contrats non signés.
    
    Args:
        db: Session de base de données
        user: Utilisateur effectuant la requête
        
    Returns:
        Liste des contrats non signés
    """
    if not has_permission(user, "contract.read"):
        raise ContractError("Vous n'avez pas la permission de consulter les contrats")
    
    return db.query(Contract).filter(Contract.is_signed == False).all()


def get_unpaid_contracts(db: Session, user: User) -> List[Contract]:
    """
    Récupère les contrats avec un solde restant.
    
    Args:
        db: Session de base de données
        user: Utilisateur effectuant la requête
        
    Returns:
        Liste des contrats non entièrement payés
    """
    if not has_permission(user, "contract.read"):
        raise ContractError("Vous n'avez pas la permission de consulter les contrats")
    
    return db.query(Contract).filter(Contract.amount_due > 0).all()


def get_my_contracts(db: Session, user: User) -> List[Contract]:
    """
    Récupère les contrats des clients du commercial connecté.
    
    Args:
        db: Session de base de données
        user: Utilisateur commercial
        
    Returns:
        Liste des contrats
    """
    if user.role != RoleEnum.SALES:
        raise ContractError("Seuls les commerciaux ont des contrats attitrés")
    
    return db.query(Contract).join(Client).filter(
        Client.sales_contact_id == user.id
    ).all()


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
        ContractError: Si permission refusée ou client non trouvé
    """
    if not has_permission(user, "contract.create"):
        raise ContractError("Vous n'avez pas la permission de créer des contrats")
    
    # Vérifier que le client existe
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise ContractError(f"Client #{client_id} non trouvé")
    
    # Un commercial ne peut créer un contrat que pour ses propres clients
    if user.role == RoleEnum.SALES and client.sales_contact_id != user.id:
        raise ContractError("Vous ne pouvez créer des contrats que pour vos clients")
    
    if amount_due is None:
        amount_due = total_amount
    
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
    total_amount: Optional[Decimal] = None,
    amount_due: Optional[Decimal] = None,
    is_signed: Optional[bool] = None
) -> Contract:
    """
    Met à jour un contrat.
    
    Args:
        db: Session de base de données
        user: Utilisateur effectuant la mise à jour
        contract_id: ID du contrat
        total_amount: Nouveau montant total (optionnel)
        amount_due: Nouveau montant dû (optionnel)
        is_signed: Nouveau statut de signature (optionnel)
        
    Returns:
        Le contrat mis à jour
        
    Raises:
        ContractError: Si permission refusée ou contrat non trouvé
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
    
    # Appliquer les modifications
    if total_amount is not None:
        contract.total_amount = total_amount
    if amount_due is not None:
        contract.amount_due = amount_due
    if is_signed is not None:
        contract.is_signed = is_signed
    
    db.commit()
    db.refresh(contract)
    
    return contract


def sign_contract(db: Session, user: User, contract_id: int) -> Contract:
    """
    Signe un contrat (raccourci pour update avec is_signed=True).
    
    Args:
        db: Session de base de données
        user: Utilisateur effectuant la signature
        contract_id: ID du contrat
        
    Returns:
        Le contrat signé
    """
    return update_contract(db, user, contract_id, is_signed=True)


def record_payment(
    db: Session,
    user: User,
    contract_id: int,
    amount: Decimal
) -> Contract:
    """
    Enregistre un paiement sur un contrat.
    
    Args:
        db: Session de base de données
        user: Utilisateur effectuant l'enregistrement
        contract_id: ID du contrat
        amount: Montant du paiement
        
    Returns:
        Le contrat mis à jour
        
    Raises:
        ContractError: Si le montant est invalide
    """
    contract = get_contract_by_id(db, user, contract_id)
    
    if amount <= 0:
        raise ContractError("Le montant du paiement doit être positif")
    
    new_amount_due = contract.amount_due - amount
    if new_amount_due < 0:
        raise ContractError(
            f"Le paiement ({amount}) dépasse le montant restant dû ({contract.amount_due})"
        )
    
    return update_contract(db, user, contract_id, amount_due=new_amount_due)
