"""Vues pour l'authentification."""

import typer
from epicevents.sentry_config import SentryTyper
from epicevents.controllers.auth_controller import (
    authenticate_user,
    register_user,
    AuthenticationError,
)
from epicevents.models import RoleEnum
from epicevents.utils import clear_token


def create_auth_app() -> SentryTyper:
    """Créer l'application Typer pour les commandes d'authentification."""
    app = SentryTyper()

    @app.command()
    def login(email: str, password: str):
        """Authentification utilisateur."""
        try:
            user, token = authenticate_user(email, password)
            typer.echo("Connexion reussie")
        except AuthenticationError as e:
            typer.echo(f"Erreur: {e}")
            raise typer.Exit(1)

    @app.command()
    def logout():
        """Deconnexion utilisateur."""
        clear_token()
        typer.echo("Deconnexion reussie")

    @app.command()
    def register(
        employee_number: str, full_name: str, email: str, password: str, role: RoleEnum
    ):
        """Inscription d'un nouveau collaborateur."""
        try:
            user = register_user(employee_number, full_name, email, password, role)
            typer.echo(f"Compte cree avec succes: {user.full_name} ({user.email})")
            typer.echo(
                "Vous pouvez maintenant vous connecter avec: python epicevents.py login"
            )
        except ValueError as e:
            typer.echo(f"Erreur: {e}")
            raise typer.Exit(1)

    return app
