"""Interface CLI pour Epic Events CRM."""

import typer
from typing import Optional
from datetime import datetime, timezone
from decimal import Decimal

from epicevents.sentry_config import init_sentry
from epicevents.database import get_db
from epicevents.controllers.auth_controller import (
    authenticate_user,
    get_authenticated_user,
    create_user,
    update_user,
    register_user,
    delete_user,
    AuthenticationError,
)
from epicevents.controllers.client_controller import (
    get_all_clients,
    create_client,
    delete_client,
)
from epicevents.controllers.contract_controller import (
    get_all_contracts,
    create_contract,
    update_contract,
    delete_contract,
)
from epicevents.controllers.event_controller import (
    get_all_events,
    create_event,
    update_event,
    delete_event,
)
from epicevents.models import RoleEnum, User
from epicevents.utils import clear_token

# Initialiser Sentry au démarrage de l'application
init_sentry()

app = typer.Typer()
user_app = typer.Typer()
client_app = typer.Typer()
contract_app = typer.Typer()
event_app = typer.Typer()

app.add_typer(user_app, name="user")
app.add_typer(client_app, name="client")
app.add_typer(contract_app, name="contract")
app.add_typer(event_app, name="event")


# AUTH
@app.command()
def login(email: str, password: str):
    """Authentification utilisateur."""
    with get_db() as db:
        try:
            user, token = authenticate_user(db, email, password)
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
    with get_db() as db:
        try:
            user = register_user(db, employee_number, full_name, email, password, role)
            typer.echo(f"Compte cree avec succes: {user.full_name} ({user.email})")
            typer.echo(
                "Vous pouvez maintenant vous connecter avec: python epicevents.py login"
            )
        except ValueError as e:
            typer.echo(f"Erreur: {e}")
            raise typer.Exit(1)
        except Exception as e:
            typer.echo(f"Erreur: {e}")
            raise typer.Exit(1)


@app.command()
def test_sentry():
    """Commande de test pour vérifier que Sentry capture bien les erreurs."""
    typer.echo("Test de Sentry - Génération d'une erreur volontaire...")
    
    # Erreur non gérée - Sentry la capturera automatiquement
    raise ValueError("Test Sentry : Cette erreur doit apparaître dans Sentry")


# USERS
@user_app.command("list")
def list_users():
    """Liste tous les utilisateurs."""
    with get_db() as db:
        try:
            user = get_authenticated_user(db)
        except AuthenticationError as e:
            typer.echo(f"Erreur: {e}")
            raise typer.Exit(1)

        users = db.query(User).all()

        typer.echo(
            f"\n{'ID':<5} {'N. Employe':<15} {'Nom':<20} {'Email':<30} {'Role':<15}"
        )
        typer.echo("-" * 90)
        for u in users:
            typer.echo(
                f"{u.id:<5} {u.employee_number:<15} {u.full_name:<20} {u.email:<30} {u.role.value:<15}"
            )

@user_app.command("create")
def create_user_cmd(
    employee_number: str, full_name: str, email: str, password: str, role: RoleEnum
):
    """Cree un utilisateur."""
    with get_db() as db:
        try:
            user = get_authenticated_user(db)
            new_user = create_user(
                db, user, employee_number, full_name, email, password, role
            )
            typer.echo(f"Utilisateur cree: {new_user.full_name}")
        except (AuthenticationError, ValueError, Exception) as e:
            typer.echo(f"Erreur: {e}")
            raise typer.Exit(1)


@user_app.command("update")
def update_user_cmd(
    employee_number: str,
    new_employee_number: Optional[str] = None,
    full_name: Optional[str] = None,
    email: Optional[str] = None,
    role: Optional[RoleEnum] = None,
):
    """Modifie un utilisateur (recherche par employee_number)."""
    with get_db() as db:
        try:
            user = get_authenticated_user(db)

            # Trouver l'utilisateur par employee_number
            target_user = (
                db.query(User).filter(User.employee_number == employee_number).first()
            )
            if not target_user:
                raise ValueError(
                    f"Utilisateur avec le numero {employee_number} non trouve"
                )

            updated = update_user(
                db,
                user,
                target_user.id,
                employee_number=new_employee_number,
                full_name=full_name,
                email=email,
                role=role,
                is_active=None,
            )
            typer.echo(f"Utilisateur modifie: {updated.full_name}")
        except (AuthenticationError, ValueError, Exception) as e:
            typer.echo(f"Erreur: {e}")
            raise typer.Exit(1)


@user_app.command("delete")
def delete_user_cmd(employee_number: str):
    """Supprime un utilisateur (recherche par employee_number)."""
    with get_db() as db:
        try:
            user = get_authenticated_user(db)

            # Trouver l'utilisateur par employee_number
            target_user = (
                db.query(User).filter(User.employee_number == employee_number).first()
            )
            if not target_user:
                raise ValueError(
                    f"Utilisateur avec le numero {employee_number} non trouve"
                )

            delete_user(db, user, target_user.id)
            typer.echo(f"Utilisateur supprime: {target_user.full_name}")
        except (AuthenticationError, ValueError, Exception) as e:
            typer.echo(f"Erreur: {e}")
            raise typer.Exit(1)


# CLIENTS
@client_app.command("list")
def list_clients():
    """Liste tous les clients."""
    with get_db() as db:
        try:
            user = get_authenticated_user(db)
            clients = get_all_clients(db, user)
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
        except (AuthenticationError, Exception) as e:
            typer.echo(f"Erreur: {e}")
            raise typer.Exit(1)

@client_app.command("create")
def create_client_cmd(full_name: str, email: str, phone: str, company_name: str):
    """Cree un client."""
    with get_db() as db:
        try:
            user = get_authenticated_user(db)
            client = create_client(db, user, full_name, email, phone, company_name)
            typer.echo(f"Client cree: ID {client.id}")
        except (AuthenticationError, ValueError, Exception) as e:
            typer.echo(f"Erreur: {e}")
            raise typer.Exit(1)


@client_app.command("delete")
def delete_client_cmd(client_id: int):
    """Supprime un client."""
    with get_db() as db:
        try:
            user = get_authenticated_user(db)
            delete_client(db, user, client_id)
            typer.echo(f"Client #{client_id} supprime")
        except (AuthenticationError, ValueError, Exception) as e:
            typer.echo(f"Erreur: {e}")
            raise typer.Exit(1)


# CONTRACTS
@contract_app.command("list")
def list_contracts():
    """Liste tous les contrats."""
    with get_db() as db:
        try:
            user = get_authenticated_user(db)
            contracts = get_all_contracts(db, user)
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
        except (AuthenticationError, Exception) as e:
            typer.echo(f"Erreur: {e}")
            raise typer.Exit(1)


@contract_app.command("create")
def create_contract_cmd(
    client_id: int, total_amount: float, amount_due: Optional[float] = None
):
    """Cree un contrat."""
    with get_db() as db:
        try:
            user = get_authenticated_user(db)
            contract = create_contract(
                db,
                user,
                client_id,
                total_amount=Decimal(str(total_amount)),
                amount_due=Decimal(str(amount_due)) if amount_due else None,
            )
            typer.echo(f"Contrat cree: ID {contract.id}")
        except (AuthenticationError, ValueError, Exception) as e:
            typer.echo(f"Erreur: {e}")
            raise typer.Exit(1)


@contract_app.command("update")
def update_contract_cmd(
    contract_id: int,
    total_amount: Optional[float] = None,
    amount_due: Optional[float] = None,
    is_signed: Optional[bool] = None,
):
    """Modifie un contrat."""
    with get_db() as db:
        try:
            user = get_authenticated_user(db)
            total_dec = Decimal(str(total_amount)) if total_amount else None
            due_dec = Decimal(str(amount_due)) if amount_due else None
            contract = update_contract(
                db,
                user,
                contract_id,
                client_id=None,
                total_amount=total_dec,
                amount_due=due_dec,
                is_signed=is_signed,
            )
            typer.echo(f"Contrat modifie: ID {contract.id}")
        except (AuthenticationError, ValueError, Exception) as e:
            typer.echo(f"Erreur: {e}")
            raise typer.Exit(1)


@contract_app.command("delete")
def delete_contract_cmd(contract_id: int):
    """Supprime un contrat."""
    with get_db() as db:
        try:
            user = get_authenticated_user(db)
            delete_contract(db, user, contract_id)
            typer.echo(f"Contrat #{contract_id} supprime")
        except (AuthenticationError, ValueError, Exception) as e:
            typer.echo(f"Erreur: {e}")
            raise typer.Exit(1)


# EVENTS
@event_app.command("list")
def list_events():
    """Liste tous les evenements."""
    with get_db() as db:
        try:
            user = get_authenticated_user(db)
            events = get_all_events(db, user)
            if events:
                typer.echo(
                    f"\n{'ID':<5} {'Client':<20} {'Lieu':<20} {'Debut':<17} {'Fin':<17} {'Part.':<6} {'Support':<20}"
                )
                typer.echo("-" * 110)
                for e in events:
                    client_name = (
                        e.contract.client.full_name
                        if e.contract and e.contract.client
                        else "N/A"
                    )
                    support_name = (
                        e.support_contact.full_name
                        if e.support_contact
                        else "Non assigné"
                    )
                    location = (e.location or "N/A")[:18]
                    typer.echo(
                        f"{e.id:<5} {client_name:<20} {location:<20} {e.event_date_start.strftime('%Y-%m-%d %H:%M'):<17} {e.event_date_end.strftime('%Y-%m-%d %H:%M'):<17} {e.attendees:<6} {support_name:<20}"
                    )
            else:
                typer.echo("Aucun evenement")
        except (AuthenticationError, Exception) as e:
            typer.echo(f"Erreur: {e}")
            raise typer.Exit(1)


@event_app.command("create")
def create_event_cmd(
    contract_id: int,
    start_date: str,
    end_date: str,
    location: str,
    attendees: int,
    notes: Optional[str] = None,
):
    """Cree un evenement (format date: YYYY-MM-DD HH:MM)."""
    with get_db() as db:
        try:
            user = get_authenticated_user(db)
            start = datetime.strptime(start_date, "%Y-%m-%d %H:%M").replace(
                tzinfo=timezone.utc
            )
            end = datetime.strptime(end_date, "%Y-%m-%d %H:%M").replace(
                tzinfo=timezone.utc
            )
            event = create_event(
                db,
                user,
                contract_id,
                event_date_start=start,
                event_date_end=end,
                location=location,
                attendees=attendees,
                notes=notes,
            )
            typer.echo(f"Evenement cree: ID {event.id}")
        except AuthenticationError as e:
            typer.echo(f"Erreur: {e}")
            raise typer.Exit(1)
        except ValueError as e:
            typer.echo(f"Erreur: {e}")
            raise typer.Exit(1)
        except Exception as e:
            typer.echo(f"Erreur: {e}")
            raise typer.Exit(1)


@event_app.command("update")
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
    with get_db() as db:
        try:
            user = get_authenticated_user(db)
            start = None
            end = None
            if start_date:
                start = datetime.strptime(start_date, "%Y-%m-%d %H:%M").replace(
                    tzinfo=timezone.utc
                )
            if end_date:
                end = datetime.strptime(end_date, "%Y-%m-%d %H:%M").replace(
                    tzinfo=timezone.utc
                )
            event = update_event(
                db,
                user,
                event_id,
                contract_id=contract_id,
                support_contact_id=support_contact_id,
                event_date_start=start,
                event_date_end=end,
                location=location,
                attendees=attendees,
                notes=notes,
            )
            typer.echo(f"Evenement modifie: ID {event.id}")
        except (AuthenticationError, ValueError, Exception) as e:
            typer.echo(f"Erreur: {e}")
            raise typer.Exit(1)


@event_app.command("delete")
def delete_event_cmd(event_id: int):
    """Supprime un evenement."""
    with get_db() as db:
        try:
            user = get_authenticated_user(db)
            delete_event(db, user, event_id)
            typer.echo(f"Evenement #{event_id} supprime")
        except (AuthenticationError, ValueError, Exception) as e:
            typer.echo(f"Erreur: {e}")
            raise typer.Exit(1)


if __name__ == "__main__":
    app()
