"""
Module de configuration Sentry pour Epic Events CRM

Ce module initialise Sentry pour la journalisation des erreurs et événements.
"""

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
    if SENTRY_DSN:
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            environment=ENVIRONMENT,
            integrations=[
                SqlalchemyIntegration(), # Trace les requêtes SQL pour le contexte des erreurs, et detecte les requetes N+1
            ],
            # Envoyer les informations de session
            auto_session_tracking=True,
            # Capture des breadcrumbs pour le contexte
            max_breadcrumbs=50,
            send_default_pii=True, # Envoie les informations personnelles identifiables (email, etc.) pour le contexte des erreurs
        )
        
        # Installer le gestionnaire d'exceptions global pour Typer
        _install_typer_exception_handler()
        
        return True
    return False

# Méthode Monkey patch pour capturer les exceptions dans les commandes Typer
def _install_typer_exception_handler():
    """
    Installe un gestionnaire d'exceptions global pour Typer.
    Toutes les exceptions non gérées dans les commandes Typer seront capturées par Sentry.
    """
    # Sauvegarder la méthode originale de typer
    original_main = typer.main.get_command
    
    # typer_instance : l'objet dans app = typer.Typer() qui contient les commandes
    # patched_get_command : wrapper qui sera appelé dès que typer crée une commande via @app.command()
    def patched_get_command(typer_instance):
        """Wrapper qui ajoute la gestion d'erreurs Sentry à toutes les commandes"""
        command = original_main(typer_instance)
        # Sauvegarde la fonction transformée en commande terminal par Typer
        original_invoke = command.invoke
        
        # On remplace la fonction d'invocation de la commande par une version qui capture les exceptions dans Sentry
        def sentry_invoke(ctx):
            """Invoke avec capture Sentry"""
            try:
                return original_invoke(ctx)
            except Exception as e:
                # Capturer l'exception dans Sentry
                sentry_sdk.capture_exception(e)
                # Relancer pour que Typer la gère normalement
                raise
        
        command.invoke = sentry_invoke
        return command
    
    # Remplacer la méthode
    typer.main.get_command = patched_get_command


def log_user_creation(user_email: str, created_by: str, role: str):
    """
    Journalise la création d'un collaborateur.
    
    Args:
        user_email: Email du collaborateur créé
        created_by: Email du créateur
        role: Rôle du collaborateur
    """
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
