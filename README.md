# Epic Events CRM

## Description

Epic Events CRM est une application de gestion de la relation client (CRM) en ligne de commande pour organiser les événements d'une entreprise événementielle. Elle permet aux équipes de vente, de support et de gestion de collaborer efficacement sur les clients, contrats et événements.

## Fonctionnalités

- **Gestion des collaborateurs** : Création, modification et suppression de collaborateurs (réservé au management)
- **Gestion des clients** : Suivi des clients et de leurs contacts commerciaux
- **Gestion des contrats** : Création, modification et signature de contrats
- **Gestion des événements** : Planification et suivi des événements avec support assigné
- **Authentification sécurisée** : Système de connexion avec JWT
- **Permissions par rôle** : Contrôle d'accès basé sur les rôles (Management, Sales, Support)
- **Journalisation Sentry** : Suivi des erreurs et des événements importants

## Prérequis

- Python 3.13+
- PostgreSQL 18+
- Un compte Sentry (optionnel, pour la journalisation des erreurs)

## Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/votre-username/OC_Epic_Events.git
cd OC_Epic_Events
```

### 2. Créer un environnement virtuel

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Configurer PostgreSQL

Créez la base de données dans PostgreSQL :

```sql
-- Connectez-vous à PostgreSQL
psql -U postgres

-- Créez la base de données
CREATE DATABASE epicevents;

-- Créez un utilisateur (optionnel, remplacer par vos propres valeurs)
CREATE USER epicevents_user WITH PASSWORD 'votre_mot_de_passe_securise';
GRANT ALL PRIVILEGES ON DATABASE epicevents TO epicevents_user;
```

### 5. Configurer les variables d'environnement

Copiez le fichier d'exemple et configurez vos propres valeurs :

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

Éditez le fichier `.env` avec vos informations :

```ini
# Configuration Base de données PostgreSQL
DB_USER=epicevents_user
DB_PASSWORD=votre_mot_de_passe_securise
DB_HOST=localhost
DB_NAME=epicevents

# Configuration Sentry (optionnel)
# Laisser vide pour désactiver Sentry
SENTRY_DSN=
ENVIRONMENT=development
```

### 6. Initialiser la base de données

Exécutez le script d'initialisation qui créera toutes les tables et un compte administrateur :

```bash
python init_db.py
```

Ce script va :
- Créer toutes les tables nécessaires (users, clients, contracts, events)
- Créer un utilisateur administrateur par défaut avec les identifiants :
  - **Numéro d'employé** : `ADMIN001`
  - **Mot de passe** : `Admin123!`
  - **Rôle** : Management

⚠️ **Important** : Changez le mot de passe après votre première connexion !

### 7. Première connexion

```bash
python epicevents.py login ADMIN001 Admin123!
```

## Configuration Sentry (Optionnel)

### Pourquoi Sentry ?

Sentry permet de :
- Capturer automatiquement toutes les exceptions de l'application
- Journaliser les événements importants (création de collaborateurs, signature de contrats)
- Suivre les performances et identifier les problèmes en production

### Configuration

1. **Créer un compte Sentry**
   - Aller sur [sentry.io](https://sentry.io) et créer un compte gratuit
   - Créer un nouveau projet Python

2. **Récupérer le DSN**
   - Dans votre projet Sentry : Settings > Client Keys (DSN)
   - Copier la valeur du DSN

3. **Configurer dans .env**
   ```ini
   SENTRY_DSN=https://votre_cle@sentry.io/votre_projet_id
   ENVIRONMENT=production
   ```

### Événements journalisés

L'application journalise automatiquement :
- ✅ **Toutes les exceptions non gérées** : Capturées automatiquement par Sentry
- ✅ **Création de collaborateur** : Quand un manager crée un nouveau collaborateur
- ✅ **Modification de collaborateur** : Quand un manager modifie un collaborateur
- ✅ **Signature de contrat** : Quand un contrat passe à l'état "signé"

### Désactiver Sentry

Pour désactiver Sentry (par exemple en développement local) :
- Laissez `SENTRY_DSN` vide dans le fichier `.env`

## Utilisation

### Authentification

```bash
# Connexion
python epicevents.py login <employee_number> <password>

# Déconnexion
python epicevents.py logout
```

### Gestion des collaborateurs (Management uniquement)

```bash
# Créer un collaborateur
python epicevents.py user create

# Lister les collaborateurs
python epicevents.py user list

# Modifier un collaborateur
python epicevents.py user update <employee_number>

# Supprimer un collaborateur
python epicevents.py user delete <employee_number>
```

### Gestion des clients

```bash
# Lister les clients
python epicevents.py client list

# Créer un client (Sales uniquement)
python epicevents.py client create

# Supprimer un client
python epicevents.py client delete <client_id>
```

### Gestion des contrats

```bash
# Lister les contrats
python epicevents.py contract list

# Créer un contrat (Sales, Management)
python epicevents.py contract create

# Modifier un contrat
python epicevents.py contract update <contract_id>

# Supprimer un contrat
python epicevents.py contract delete <contract_id>
```

### Gestion des événements

```bash
# Lister les événements
python epicevents.py event list

# Créer un événement (Sales, Management)
python epicevents.py event create

# Modifier un événement
python epicevents.py event update <event_id>

# Supprimer un événement
python epicevents.py event delete <event_id>
```

### Aide

Pour plus d'informations sur les commandes :

```bash
# Aide générale
python epicevents.py --help

# Aide sur une commande spécifique
python epicevents.py user --help
python epicevents.py client --help
```

## Rôles et Permissions

### Management (Gestion)
- **Collaborateurs** : Créer, modifier, supprimer tous les collaborateurs
- **Clients** : Toutes les opérations sur tous les clients
- **Contrats** : Toutes les opérations sur tous les contrats
- **Événements** : Toutes les opérations sur tous les événements, y compris assigner le support

### Sales (Commercial)
- **Clients** : Créer et modifier uniquement leurs propres clients
- **Contrats** : Créer et modifier uniquement les contrats de leurs clients
- **Événements** : Créer des événements uniquement pour leurs contrats signés

### Support
- **Clients** : Lecture seule de tous les clients
- **Contrats** : Lecture seule de tous les contrats
- **Événements** : Modifier uniquement les événements qui leur sont assignés

## Structure du projet

```
OC_Epic_Events/
├── epicevents/                    # Package principal
│   ├── __init__.py
│   ├── config.py                  # Configuration (DB, Sentry)
│   ├── database.py                # Configuration SQLAlchemy
│   ├── models.py                  # Modèles de données (User, Client, Contract, Event)
│   ├── permissions.py             # Système de permissions par rôle
│   ├── sentry_config.py           # Configuration et journalisation Sentry
│   ├── utils.py                   # Utilitaires (JWT, hash de mots de passe)
│   ├── controllers/               # Logique métier
│   │   ├── __init__.py
│   │   ├── auth_controller.py     # Authentification et gestion des utilisateurs
│   │   ├── client_controller.py   # Gestion des clients
│   │   ├── contract_controller.py # Gestion des contrats
│   │   └── event_controller.py    # Gestion des événements
│   └── views/                     # Interface utilisateur (future)
│       └── __init__.py
├── .env.example                   # Template de configuration
├── .gitignore                     # Fichiers à ignorer par Git
├── epicevents.py                  # Point d'entrée CLI principal
├── init_db.py                     # Script d'initialisation de la base de données
├── main.py                        # Script de démonstration/test manuel
├── pytest.ini                     # Configuration pytest (local uniquement)
├── README.md                      # Ce fichier
└── requirements.txt               # Dépendances Python
```

## Sécurité

### Bonnes pratiques implémentées

- ✅ **Mots de passe hachés** : Utilisation de bcrypt avec salage automatique
- ✅ **Tokens JWT** : Authentification par tokens stockés localement
- ✅ **Variables d'environnement** : Configuration sensible dans `.env` (non versionné)
- ✅ **DSN Sentry sécurisé** : Stocké dans les variables d'environnement
- ✅ **Permissions par rôle** : Contrôle d'accès strict avec décorateurs
- ✅ **Validation des données** : Validation des entrées utilisateur
- ✅ **Separation of concerns** : Architecture en couches (Models, Controllers, CLI)

### ⚠️ Important - Ne jamais exposer publiquement

- **Fichier .env** : Contient les identifiants de base de données et clés Sentry
- **Token d'authentification** (`.epic_token`) : Token JWT de session
- **Mots de passe** : Toujours hachés, jamais en clair

### Recommandations pour la production

1. **Utilisez des mots de passe forts** pour tous les comptes
2. **Changez le mot de passe administrateur** après la première connexion
3. **Configurez ENVIRONMENT=production** dans `.env` pour la production
4. **Activez Sentry** pour monitorer les erreurs en production
5. **Restreignez l'accès** à la base de données PostgreSQL
6. **Utilisez HTTPS** si vous déployez l'application sur un serveur distant

## Dépendances

### Principales

- **SQLAlchemy** : ORM pour la gestion de la base de données
- **psycopg2-binary** : Driver PostgreSQL
- **python-dotenv** : Gestion des variables d'environnement
- **bcrypt** : Hachage des mots de passe
- **PyJWT** : Génération et validation de tokens JWT
- **typer** : Framework CLI moderne
- **sentry-sdk** : Journalisation des erreurs et événements

Voir [requirements.txt](requirements.txt) pour la liste complète.

## Dépannage

### Erreur de connexion à la base de données

```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Solutions** :
- Vérifier que PostgreSQL est démarré
- Vérifier les variables dans `.env` (DB_USER, DB_PASSWORD, DB_HOST, DB_NAME)
- Vérifier que la base de données `epicevents` existe
- Tester la connexion : `psql -U votre_user -d epicevents`

### Sentry ne fonctionne pas

**Solutions** :
- Vérifier que `SENTRY_DSN` est bien configuré dans `.env`
- Vérifier que `sentry-sdk` est installé : `pip list | grep sentry`
- Regarder les logs au démarrage de l'application
- Tester avec une erreur volontaire pour vérifier l'envoi à Sentry

### Erreur de permission

```
PermissionError: Vous n'avez pas la permission...
```

**Solutions** :
- Vérifier que vous êtes connecté : `python epicevents.py login`
- Vérifier votre rôle pour l'action demandée (voir section Rôles et Permissions)
- Contacter un administrateur pour modifier vos permissions

### Module introuvable

```
ModuleNotFoundError: No module named 'epicevents'
```

**Solutions** :
- Vérifier que vous êtes dans le bon répertoire
- Vérifier que l'environnement virtuel est activé
- Réinstaller les dépendances : `pip install -r requirements.txt`

## Développement

### Ajouter une nouvelle fonctionnalité avec journalisation Sentry

Pour journaliser un nouvel événement dans Sentry :

1. Créer une fonction dans [epicevents/sentry_config.py](epicevents/sentry_config.py)
2. L'appeler depuis le contrôleur approprié
3. Utiliser `sentry_sdk.capture_message()` pour les événements
4. Utiliser `sentry_sdk.capture_exception()` pour les erreurs

**Exemple** :

```python
# Dans sentry_config.py
def log_custom_event(event_name: str, details: dict):
    """Journalise un événement personnalisé"""
    if not sentry_sdk.Hub.current.client:
        return
    
    sentry_sdk.capture_message(
        f"Événement personnalisé : {event_name}",
        level="info",
        extras=details
    )

# Dans votre contrôleur
from epicevents.sentry_config import log_custom_event

log_custom_event("nouvelle_action", {
    "user": user.email,
    "action": "description"
})
```

## Auteur

Projet réalisé par Noam dans le cadre du Projet 12 - OpenClassrooms

## Licence

Ce projet est un projet éducatif pour OpenClassrooms.


