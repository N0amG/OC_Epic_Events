"""Vues pour la gestion des clients."""

import typer
from epicevents.sentry_config import SentryTyper
from epicevents.controllers.auth_controller import AuthenticationError
from epicevents.controllers.client_controller import (
    get_all_clients,
    create_client,
    delete_client,
    ClientError,
)


def create_client_app() -> SentryTyper:
    """Créer l'application Typer pour les commandes clients."""
    app = SentryTyper()

    @app.command("list")
    def list_clients():
        """Liste tous les clients."""
        try:
            clients = get_all_clients()
            if clients:
                typer.echo(
                    f"\n{'ID':<5} {'Nom':<25} {'Email':<30} {'Telephone':<15} {'Societe':<20} {'Contact Commercial':<20}"
                )
                typer.echo("-" * 120)
                for c in clients:
                    phone = c.phone or "N/A"
                    company = c.company_name or "N/A"
                    contact = c.sales_contact.full_name if c.sales_contact else "N/A"
                    typer.echo(
                        f"{c.id:<5} {c.full_name:<25} {c.email:<30} {phone:<15} {company:<20} {contact:<20}"
                    )
            else:
                typer.echo("Aucun client")
        except (AuthenticationError, ClientError) as e:
            typer.echo(f"Erreur: {e}")
            raise typer.Exit(1)

    @app.command("create")
    def create_client_cmd(full_name: str, email: str, phone: str, company_name: str):
        """Cree un client."""
        try:
            client = create_client(full_name, email, phone, company_name)
            typer.echo(f"Client cree: ID {client.id}")
        except (AuthenticationError, ClientError, ValueError) as e:
            typer.echo(f"Erreur: {e}")
            raise typer.Exit(1)

    @app.command("delete")
    def delete_client_cmd(client_id: int):
        """Supprime un client."""
        try:
            delete_client(client_id)
            typer.echo(f"Client #{client_id} supprime")
        except (AuthenticationError, ClientError, ValueError) as e:
            typer.echo(f"Erreur: {e}")
            raise typer.Exit(1)

    return app
