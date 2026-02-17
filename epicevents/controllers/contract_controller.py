"""
Contrôleur Contract pour Epic Events CRM

Ce module gère la lecture, création et mise à jour des contrats.
"""

from typing import List, Optional
from decimal import Decimal
from sqlalchemy.orm import Session, joinedload

from epicevents.models import Contract, Client, User, RoleEnum
from epicevents.permissions import has_permission
from epicevents.sentry_config import log_contract_signature
from epicevents.database import get_db
from epicevents.controllers.auth_controller import get_authenticated_user


class ContractError(Exception):
    """Exception levée pour les erreurs liées aux contrats."""

    pass


def get_all_contracts() -> List[Contract]:
    """
    Récupère tous les contrats.

    Returns:
        Liste des contrats

    Raises:
        AuthenticationError: Si non authentifié
        ContractError: Si l'utilisateur n'a pas la permission
    """
    with get_db() as db:
        user = get_authenticated_user(db)
        if not has_permission(user, "contract.read"):
            raise ContractError("Vous n'avez pas la permission de consulter les contrats")

        return db.query(Contract).options(joinedload(Contract.client)).all()


def create_contract(
    client_id: int,
    total_amount: float,
    amount_due: Optional[float] = None,
) -> Contract:
    """
    Crée un nouveau contrat.

    Args:
        client_id: ID du client
        total_amount: Montant total du contrat (float)
        amount_due: Montant restant dû (float, par défaut = total_amount)

    Returns:
        Le contrat créé

    Raises:
        AuthenticationError: Si non authentifié
        ContractError: Si permission refusée ou données invalides
    """
    with get_db() as db:
        user = get_authenticated_user(db)
        
        # Vérifier les permissions
        if not has_permission(user, "contract.create"):
            raise ContractError("Vous n'avez pas la permission de créer des contrats")

        # Convertir float en Decimal
        total_amount_dec = Decimal(str(total_amount))
        amount_due_dec = Decimal(str(amount_due)) if amount_due is not None else None

        # Validation des données
        if total_amount_dec <= 0:
            raise ContractError("Le montant total doit être positif")

        # Vérifier que le client existe
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise ContractError(f"Client #{client_id} non trouvé")

        # Un commercial ne peut créer un contrat que pour ses propres clients
        if user.role == RoleEnum.SALES and client.sales_contact_id != user.id:
            raise ContractError("Vous ne pouvez créer des contrats que pour vos clients")

        if amount_due_dec is None:
            amount_due_dec = total_amount_dec

        if amount_due_dec < 0 or amount_due_dec > total_amount_dec:
            raise ContractError("Le montant dû doit être entre 0 et le montant total")

        # Créer le contrat
        contract = Contract(
            client_id=client_id,
            total_amount=total_amount_dec,
            amount_due=amount_due_dec,
            is_signed=False,
        )

        db.add(contract)
        db.commit()
        db.refresh(contract)
        return contract


def update_contract(
    contract_id: int,
    client_id: Optional[int] = None,
    total_amount: Optional[float] = None,
    amount_due: Optional[float] = None,
    is_signed: Optional[bool] = None,
) -> Contract:
    """
    Met à jour un contrat (tous les champs, y compris relationnels).

    Args:
        contract_id: ID du contrat
        client_id: Nouveau client (champ relationnel)
        total_amount: Nouveau montant total (float)
        amount_due: Nouveau montant dû (float)
        is_signed: Nouveau statut de signature

    Returns:
        Le contrat mis à jour

    Raises:
        AuthenticationError: Si non authentifié
        ContractError: Si permission refusée ou données invalides
    """
    with get_db() as db:
        user = get_authenticated_user(db)
        
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
            total_amount_dec = Decimal(str(total_amount))
            if total_amount_dec <= 0:
                raise ContractError("Le montant total doit être positif")
            contract.total_amount = total_amount_dec

        if amount_due is not None:
            amount_due_dec = Decimal(str(amount_due))
            if amount_due_dec < 0:
                raise ContractError("Le montant dû ne peut pas être négatif")
            if amount_due_dec > contract.total_amount:
                raise ContractError("Le montant dû ne peut pas dépasser le montant total")
            contract.amount_due = amount_due_dec

        if is_signed is not None:
            # Vérifier si le contrat passe de non signé à signé
            was_unsigned = not contract.is_signed
            contract.is_signed = is_signed

            # Journaliser la signature du contrat
            if was_unsigned and is_signed:
                client_name = (
                    contract.client.company_name if contract.client else "Client inconnu"
                )
                log_contract_signature(
                    contract_id=contract.id,
                    client_name=client_name,
                    signed_by=user.email,
                    total_amount=float(contract.total_amount),
                )

        db.commit()
        db.refresh(contract)

        return contract


def delete_contract(contract_id: int) -> bool:
    """
    Supprime un contrat.

    Args:
        contract_id: ID du contrat à supprimer

    Returns:
        True si la suppression a réussi

    Raises:
        AuthenticationError: Si non authentifié
        ContractError: Si permission refusée ou contrat non trouvé
    """
    with get_db() as db:
        user = get_authenticated_user(db)
        
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            raise ContractError(f"Contrat #{contract_id} non trouvé")

        # Vérifier les permissions
        can_delete = False
        if has_permission(user, "contract.delete"):
            can_delete = True
        elif has_permission(user, "contract.delete_own"):
            if contract.client and contract.client.sales_contact_id == user.id:
                can_delete = True

        if not can_delete:
            raise ContractError("Vous n'avez pas la permission de supprimer ce contrat")

        db.delete(contract)
        db.commit()

        return True
