"""
Module de configuration Sentry pour Epic Events CRM

Ce module initialise Sentry pour la journalisation des erreurs et événements.
"""

import functools
import sentry_sdk
import typer
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from epicevents.config import SENTRY_DSN, ENVIRONMENT


def init_sentry():
    """
    Initialise Sentry pour la journalisation.
    
    Journalise :
    - Toutes les exceptions inattendues
    - Les événements personnalisés (création/modification de collaborateurs, signature de contrats)
    
    Ne s'initialise que si SENTRY_DSN est configuré.
    """
    # Vérifier que SENTRY_DSN est défini (config.py le nettoie déjà)
    if SENTRY_DSN:
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            environment=ENVIRONMENT,
            integrations=[
                SqlalchemyIntegration(), # Trace les requêtes SQL pour le contexte des erreurs, et detecte les requetes N+1
            ],
            auto_session_tracking=True, # Traque automatiquement les sessions pour mieux comprendre les erreurs liées à l'authentification
            # Capture des breadcrumbs pour le contexte
            max_breadcrumbs=50,
            send_default_pii=True, # Envoie les informations personnelles identifiables (email, etc.) pour le contexte des erreurs
        )
        
        return True
    return False


def sentry_cli_command(func):
    """
    Décorateur pour les commandes CLI Typer.
    
    Capture automatiquement les erreurs inattendues dans Sentry.
    
    Fonctionnement :
    - --help ne déclenche aucun envoi (Typer gère le help AVANT d'appeler la fonction).
    - Les erreurs métier (ValueError, AuthenticationError, etc.) sont gérées
      par try/except dans les commandes et ne remontent pas ici.
    - Seules les erreurs inattendues (bugs, 1/0, etc.) remontent au décorateur
      et sont envoyées à Sentry.
    
    Usage:
        @app.command()
        @sentry_cli_command
        def ma_commande():
            ...
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (SystemExit, KeyboardInterrupt):
            # typer.Exit() ou Ctrl+C : comportement normal, on ne touche pas
            raise
        except Exception as e:
            # Erreur inattendue (bug) : on envoie à Sentry puis on re-raise
            # Ne capturer que si Sentry est configuré
            if SENTRY_DSN:
                sentry_sdk.capture_exception(e)
            raise
    return wrapper


class SentryTyper(typer.Typer):
    """
    Sous-classe de typer.Typer qui applique automatiquement le décorateur
    sentry_cli_command à toutes les commandes enregistrées.
    
    Cela évite de devoir ajouter @sentry_cli_command manuellement
    sur chaque commande.
    
    Si Sentry n'est pas configuré (SENTRY_DSN vide ou absent),
    se comporte exactement comme typer.Typer standard.
    
    Usage:
        app = SentryTyper()  # au lieu de typer.Typer()
        
        @app.command()
        def ma_commande():   # automatiquement wrappée par Sentry si configuré
            ...
    """
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("add_completion", False)
        super().__init__(*args, **kwargs)

    def command(self, *args, **kwargs):
        """Surcharge de command() pour wrapper automatiquement avec sentry_cli_command."""
        parent_decorator = super().command(*args, **kwargs)
        
        # Si Sentry n'est pas configuré, comportement normal de Typer
        if not SENTRY_DSN:
            return parent_decorator
        
        # Sinon, wrapper avec Sentry
        def decorator(func):
            return parent_decorator(sentry_cli_command(func))
        return decorator


def log_user_creation(user_email: str, created_by: str, role: str):
    """
    Journalise la création d'un collaborateur.
    
    Args:
        user_email: Email du collaborateur créé
        created_by: Email du créateur
        role: Rôle du collaborateur
    """
    if not SENTRY_DSN:
        return
    
    sentry_sdk.capture_message(
        f"Nouveau collaborateur créé : {user_email}",
        level="info",
        extras={
            "user_email": user_email,
            "created_by": created_by,
            "role": role,
            "action": "user_creation",
        },
    )


def log_user_update(user_email: str, updated_by: str, changes: dict):
    """
    Journalise la modification d'un collaborateur.
    
    Args:
        user_email: Email du collaborateur modifié
        updated_by: Email de celui qui a fait la modification
        changes: Dictionnaire des modifications effectuées
    """
    if not SENTRY_DSN:
        return
    
    sentry_sdk.capture_message(
        f"Collaborateur modifié : {user_email}",
        level="info",
        extras={
            "user_email": user_email,
            "updated_by": updated_by,
            "changes": changes,
            "action": "user_update",
        },
    )


def log_contract_signature(contract_id: int, client_name: str, signed_by: str, total_amount: float):
    """
    Journalise la signature d'un contrat.
    
    Args:
        contract_id: ID du contrat
        client_name: Nom du client
        signed_by: Email de celui qui a signé
        total_amount: Montant total du contrat
    """
    if not SENTRY_DSN:
        return
    
    sentry_sdk.capture_message(
        f"Contrat #{contract_id} signé pour {client_name}",
        level="info",
        extras={
            "contract_id": contract_id,
            "client_name": client_name,
            "signed_by": signed_by,
            "total_amount": total_amount,
            "action": "contract_signature",
        },
    )
