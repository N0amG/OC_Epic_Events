# Epic Events CRM

## Description

Epic Events CRM est une application de gestion de la relation client (CRM) pour organiser les événements. Elle permet aux équipes de vente, de support et de gestion de collaborer efficacement sur les clients, contrats et événements.

## Fonctionnalités

- **Gestion des collaborateurs** : Création, modification et suppression de collaborateurs (réservé au management)
- **Gestion des clients** : Suivi des clients et de leurs contacts commerciaux
- **Gestion des contrats** : Création, modification et signature de contrats
- **Gestion des événements** : Planification et suivi des événements avec support assigné
- **Authentification sécurisée** : Système de connexion avec JWT
- **Permissions par rôle** : Contrôle d'accès basé sur les rôles (Management, Sales, Support)
- **Journalisation Sentry** : Suivi des erreurs et des événements importants

## Prérequis

- Python 3.8+
- PostgreSQL
- Un compte Sentry (optionnel, pour la journalisation)

## Installation

1. **Cloner le dépôt**
   ```bash
   git clone <votre-repo>
   cd OC_Epic_Events
   ```

2. **Créer un environnement virtuel**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # ou
   source .venv/bin/activate  # Linux/Mac
   ```

3. **Installer les dépendances**
   ```bash
   pip install -r requierements.txt
   ```

4. **Configurer les variables d'environnement**
   - Copier le fichier `.env.example` vers `.env`
   - Éditer `.env` avec vos propres valeurs :
   ```bash
   cp .env.example .env
   ```
   
   Variables à configurer :
   - `DB_USER` : Nom d'utilisateur PostgreSQL
   - `DB_PASSWORD` : Mot de passe PostgreSQL
   - `DB_HOST` : Hôte de la base de données (généralement `localhost`)
   - `DB_NAME` : Nom de la base de données
   - `SENTRY_DSN` : DSN Sentry (optionnel, laissez vide pour désactiver)
   - `ENVIRONMENT` : Environnement (development, staging, production)

5. **Créer la base de données**
   ```sql
   CREATE DATABASE epicevents;
   ```

6. **Initialiser les tables**
   ```bash
   python main.py
   ```

## Configuration Sentry

### Pourquoi Sentry ?

Sentry permet de :
- Capturer automatiquement toutes les exceptions de l'application
- Journaliser les événements importants (création de collaborateurs, signature de contrats)
- Suivre les performances et identifier les problèmes en production

### Configuration

1. **Créer un compte Sentry**
   - Aller sur [sentry.io](https://sentry.io)
   - Créer un nouveau projet Python

2. **Récupérer le DSN**
   - Dans votre projet Sentry, aller dans Settings > Client Keys (DSN)
   - Copier la valeur du DSN

3. **Configurer dans .env**
   ```
   SENTRY_DSN=https://your-key@sentry.io/your-project-id
   ENVIRONMENT=production
   ```

### Événements journalisés

L'application journalise automatiquement :
- ✅ **Toutes les exceptions inattendues** : Capturées automatiquement par Sentry
- ✅ **Création de collaborateur** : Quand un manager crée un nouveau collaborateur
- ✅ **Modification de collaborateur** : Quand un manager modifie un collaborateur existant
- ✅ **Signature de contrat** : Quand un contrat passe à l'état "signé"

### Désactiver Sentry

Pour désactiver Sentry (par exemple en développement local) :
- Laissez `SENTRY_DSN` vide dans le fichier `.env`
- Ou commentez la ligne dans `.env`

## Utilisation

### Authentification

```bash
# Connexion
python epicevents.py login <email> <password>

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
python epicevents.py user update <user_id>

# Supprimer un collaborateur
python epicevents.py user delete <user_id>
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

## Rôles et Permissions

### Management
- Créer/modifier/supprimer des collaborateurs
- Toutes les opérations sur clients, contrats et événements
- Assigner des contacts de support

### Sales (Commercial)
- Créer/modifier ses propres clients
- Créer/modifier les contrats de ses clients
- Créer des événements pour ses contrats signés

### Support
- Voir tous les clients et contrats
- Modifier les événements qui leur sont assignés

## Structure du projet

```
OC_Epic_Events/
├── epicevents/
│   ├── __init__.py
│   ├── config.py              # Configuration (DB, Sentry)
│   ├── database.py            # Configuration SQLAlchemy
│   ├── models.py              # Modèles de données
│   ├── permissions.py         # Système de permissions
│   ├── sentry_config.py       # Configuration Sentry ✨ NOUVEAU
│   ├── utils.py               # Utilitaires (JWT, hash)
│   ├── controllers/
│   │   ├── auth_controller.py       # Authentification
│   │   ├── client_controller.py     # Gestion clients
│   │   ├── contract_controller.py   # Gestion contrats
│   │   └── event_controller.py      # Gestion événements
│   └── views/
├── tests/                     # Tests unitaires
├── .env.example              # Template de configuration ✨ NOUVEAU
├── .gitignore
├── epicevents.py             # Interface CLI
├── main.py                   # Script de test
├── README.md                 # Ce fichier
└── requierements.txt         # Dépendances
```

## Sécurité

### Bonnes pratiques implémentées

- ✅ **Mots de passe hachés** : Utilisation de bcrypt
- ✅ **Tokens JWT** : Authentification par tokens
- ✅ **Variables d'environnement** : Configuration sensible dans `.env`
- ✅ **Fichier .env ignoré** : Non versionné dans Git
- ✅ **DSN Sentry sécurisé** : Stocké dans les variables d'environnement
- ✅ **Permissions par rôle** : Contrôle d'accès strict

### ⚠️ Important

- **Ne jamais commit le fichier `.env`** : Il contient des informations sensibles
- **Ne pas partager le DSN Sentry** : C'est une clé privée
- **Changer les secrets en production** : Utiliser des valeurs fortes et uniques

## Tests

```bash
# Installer les dépendances de test
pip install -r requirements-test.txt

# Exécuter les tests
pytest

# Avec couverture
pytest --cov=epicevents
```

## Développement

### Ajouter une nouvelle fonctionnalité journalisée

Pour journaliser un nouvel événement dans Sentry :

1. Créer une fonction dans [sentry_config.py](epicevents/sentry_config.py)
2. L'appeler depuis le contrôleur approprié
3. Utiliser `sentry_sdk.capture_message()` pour les événements
4. Utiliser `sentry_sdk.capture_exception()` pour les erreurs

Exemple :
```python
from epicevents.sentry_config import log_contract_signature

# Dans votre contrôleur
if contract.is_signed:
    log_contract_signature(
        contract_id=contract.id,
        client_name=client.company_name,
        signed_by=user.email,
        total_amount=float(contract.total_amount)
    )
```

## Dépannage

### Erreur de connexion à la base de données
- Vérifier que PostgreSQL est démarré
- Vérifier les variables dans `.env`
- Vérifier que la base `epicevents` existe

### Sentry ne fonctionne pas
- Vérifier que `SENTRY_DSN` est bien configuré dans `.env`
- Vérifier que `sentry-sdk` est installé
- Regarder les logs au démarrage de l'application

### Erreur de permission
- Vérifier que vous êtes connecté (`python epicevents.py login`)
- Vérifier votre rôle pour l'action demandée

## Contribution

1. Créer une branche pour votre fonctionnalité
2. Commiter vos changements
3. Écrire des tests
4. Créer une Pull Request

## Licence

Ce projet est un projet éducatif pour OpenClassrooms.
