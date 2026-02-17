"""Interface CLI pour Epic Events CRM."""

from epicevents.sentry_config import init_sentry
from epicevents.views.auth_views import create_auth_app
from epicevents.views.user_views import create_user_app
from epicevents.views.client_views import create_client_app
from epicevents.views.contract_views import create_contract_app
from epicevents.views.event_views import create_event_app

# Initialiser Sentry au démarrage de l'application
init_sentry()

# Créer l'application principale et les sous-applications
app = create_auth_app()
app.add_typer(create_user_app(), name="user")
app.add_typer(create_client_app(), name="client")
app.add_typer(create_contract_app(), name="contract")
app.add_typer(create_event_app(), name="event")

if __name__ == "__main__":
    app()
