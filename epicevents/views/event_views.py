"""Vues pour la gestion des événements."""

import typer
from typing import Optional
from epicevents.sentry_config import SentryTyper
from epicevents.controllers.auth_controller import AuthenticationError
from epicevents.controllers.event_controller import (
    get_all_events,
    create_event,
    update_event,
    delete_event,
    EventError,
)


def create_event_app() -> SentryTyper:
    """Créer l'application Typer pour les commandes événements."""
    app = SentryTyper()

    @app.command("list")
    def list_events():
        """Liste tous les evenements."""
        try:
            events = get_all_events()
            if events:
                typer.echo(
                    f"\n{'ID':<5} {'Client':<20} {'Lieu':<20} {'Debut':<17} {'Fin':<17} {'Part.':<6} {'Support':<20}"
                )
                typer.echo("-" * 110)
                for e in events:
                    typer.echo(
                        f"{e['id']:<5} {e['client_name']:<20} {e['location']:<20} {e['start']:<17} {e['end']:<17} {e['attendees']:<6} {e['support']:<20}"
                    )
            else:
                typer.echo("Aucun evenement")
        except (AuthenticationError, EventError) as e:
            typer.echo(f"Erreur: {e}")
            raise typer.Exit(1)

    @app.command("create")
    def create_event_cmd(
        contract_id: int,
        start_date: str,
        end_date: str,
        location: str,
        attendees: int,
        notes: Optional[str] = None,
    ):
        """Cree un evenement (format date: YYYY-MM-DD HH:MM)."""
        try:
            event = create_event(
                contract_id,
                event_date_start=start_date,
                event_date_end=end_date,
                location=location,
                attendees=attendees,
                notes=notes,
            )
            typer.echo(f"Evenement cree: ID {event.id}")
        except (AuthenticationError, EventError, ValueError) as e:
            typer.echo(f"Erreur: {e}")
            raise typer.Exit(1)

    @app.command("update")
    def update_event_cmd(
        event_id: int,
        contract_id: Optional[int] = None,
        support_contact_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[int] = None,
        notes: Optional[str] = None,
    ):
        """Modifie un evenement (format date: YYYY-MM-DD HH:MM)."""
        try:
            event = update_event(
                event_id,
                contract_id=contract_id,
                support_contact_id=support_contact_id,
                event_date_start=start_date,
                event_date_end=end_date,
                location=location,
                attendees=attendees,
                notes=notes,
            )
            typer.echo(f"Evenement modifie: ID {event.id}")
        except (AuthenticationError, EventError, ValueError) as e:
            typer.echo(f"Erreur: {e}")
            raise typer.Exit(1)

    @app.command("delete")
    def delete_event_cmd(event_id: int):
        """Supprime un evenement."""
        try:
            delete_event(event_id)
            typer.echo(f"Evenement #{event_id} supprime")
        except (AuthenticationError, EventError, ValueError) as e:
            typer.echo(f"Erreur: {e}")
            raise typer.Exit(1)

    return app
