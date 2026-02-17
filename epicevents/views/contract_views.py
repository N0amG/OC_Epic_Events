"""Vues pour la gestion des contrats."""

import typer
from typing import Optional
from epicevents.sentry_config import SentryTyper
from epicevents.controllers.auth_controller import AuthenticationError
from epicevents.controllers.contract_controller import (
    get_all_contracts,
    create_contract,
    update_contract,
    delete_contract,
    ContractError,
)


def create_contract_app() -> SentryTyper:
    """Créer l'application Typer pour les commandes contrats."""
    app = SentryTyper()

    @app.command("list")
    def list_contracts():
        """Liste tous les contrats."""
        try:
            contracts = get_all_contracts()
            if contracts:
                typer.echo(
                    f"\n{'ID':<5} {'Client':<25} {'Montant':<12} {'Du':<12} {'Signe':<8}"
                )
                typer.echo("-" * 70)
                for c in contracts:
                    client_name = c.client.full_name if c.client else "N/A"
                    typer.echo(
                        f"{c.id:<5} {client_name:<25} {float(c.total_amount):<12.2f} {float(c.amount_due):<12.2f} {'Oui' if c.is_signed else 'Non':<8}"
                    )
            else:
                typer.echo("Aucun contrat")
        except (AuthenticationError, ContractError) as e:
            typer.echo(f"Erreur: {e}")
            raise typer.Exit(1)

    @app.command("create")
    def create_contract_cmd(
        client_id: int, total_amount: float, amount_due: Optional[float] = None
    ):
        """Cree un contrat."""
        try:
            contract = create_contract(client_id, total_amount=total_amount, amount_due=amount_due)
            typer.echo(f"Contrat cree: ID {contract.id}")
        except (AuthenticationError, ContractError, ValueError) as e:
            typer.echo(f"Erreur: {e}")
            raise typer.Exit(1)

    @app.command("update")
    def update_contract_cmd(
        contract_id: int,
        total_amount: Optional[float] = None,
        amount_due: Optional[float] = None,
        is_signed: Optional[bool] = None,
    ):
        """Modifie un contrat."""
        try:
            contract = update_contract(
                contract_id,
                client_id=None,
                total_amount=total_amount,
                amount_due=amount_due,
                is_signed=is_signed,
            )
            typer.echo(f"Contrat modifie: ID {contract.id}")
        except (AuthenticationError, ContractError, ValueError) as e:
            typer.echo(f"Erreur: {e}")
            raise typer.Exit(1)

    @app.command("delete")
    def delete_contract_cmd(contract_id: int):
        """Supprime un contrat."""
        try:
            delete_contract(contract_id)
            typer.echo(f"Contrat #{contract_id} supprime")
        except (AuthenticationError, ContractError, ValueError) as e:
            typer.echo(f"Erreur: {e}")
            raise typer.Exit(1)

    return app
