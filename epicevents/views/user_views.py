"""Vues pour la gestion des utilisateurs."""

import typer
from typing import Optional
from epicevents.sentry_config import SentryTyper
from epicevents.controllers.auth_controller import AuthenticationError
from epicevents.controllers.user_controller import (
    get_all_users,
    create_user,
    update_user,
    delete_user,
)
from epicevents.models import RoleEnum


def create_user_app() -> SentryTyper:
    """Créer l'application Typer pour les commandes utilisateurs."""
    app = SentryTyper()

    @app.command("list")
    def list_users():
        """Liste tous les utilisateurs."""
        try:
            users = get_all_users()
            typer.echo(
                f"\n{'ID':<5} {'N. Employe':<15} {'Nom':<20} {'Email':<30} {'Role':<15}"
            )
            typer.echo("-" * 90)
            for u in users:
                typer.echo(
                    f"{u['id']:<5} {u['employee_number']:<15} {u['full_name']:<20} {u['email']:<30} {u['role']:<15}"
                )
        except AuthenticationError as e:
            typer.echo(f"Erreur: {e}")
            raise typer.Exit(1)

    @app.command("create")
    def create_user_cmd(
        employee_number: str, full_name: str, email: str, password: str, role: RoleEnum
    ):
        """Cree un utilisateur."""
        try:
            new_user = create_user(employee_number, full_name, email, password, role)
            typer.echo(f"Utilisateur cree: {new_user.full_name}")
        except (AuthenticationError, ValueError) as e:
            typer.echo(f"Erreur: {e}")
            raise typer.Exit(1)

    @app.command("update")
    def update_user_cmd(
        employee_number: str,
        new_employee_number: Optional[str] = None,
        full_name: Optional[str] = None,
        email: Optional[str] = None,
        role: Optional[RoleEnum] = None,
    ):
        """Modifie un utilisateur (recherche par employee_number)."""
        try:
            updated = update_user(
                employee_number,
                new_employee_number=new_employee_number,
                full_name=full_name,
                email=email,
                role=role,
                is_active=None,
            )
            typer.echo(f"Utilisateur modifie: {updated.full_name}")
        except (AuthenticationError, ValueError) as e:
            typer.echo(f"Erreur: {e}")
            raise typer.Exit(1)

    @app.command("delete")
    def delete_user_cmd(employee_number: str):
        """Supprime un utilisateur (recherche par employee_number)."""
        try:
            delete_user(employee_number)
            typer.echo(f"Utilisateur supprime")
        except (AuthenticationError, ValueError) as e:
            typer.echo(f"Erreur: {e}")
            raise typer.Exit(1)

    return app
