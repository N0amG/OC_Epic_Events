"""
Contrôleur d'authentification pour Epic Events CRM

Ce module gère :
- L'inscription des collaborateurs
- La connexion (authentification)
- La vérification des sessions
"""

from typing import Optional, Tuple, List
from sqlalchemy.orm import Session

from epicevents.models import User, RoleEnum
from epicevents.sentry_config import log_user_creation, log_user_update
from epicevents.database import get_db
from epicevents.utils import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    save_token,
    clear_token,
    get_valid_token,
)


class AuthenticationError(Exception):
    """Exception levée lors d'une erreur d'authentification"""

    pass


class AuthorizationError(Exception):
    """Exception levée lors d'une erreur d'autorisation"""

    pass


def register_user(
    employee_number: str,
    full_name: str,
    email: str,
    password: str,
    role: RoleEnum,
) -> User:
    """
    Inscrit un nouveau collaborateur.

    Args:
        employee_number: Numéro d'employé unique
        full_name: Nom complet
        email: Adresse email
        password: Mot de passe en clair (sera haché)
        role: Rôle du collaborateur

    Returns:
        L'utilisateur créé

    Raises:
        ValueError: Si l'email ou le numéro d'employé existe déjà
    """
    with get_db() as db:
        # Vérifier si l'email existe déjà
        existing_email = db.query(User).filter(User.email == email.lower()).first()
        if existing_email:
            raise ValueError("Cette adresse email est déjà utilisée")

        # Vérifier si le numéro d'employé existe déjà
        existing_employee = (
            db.query(User).filter(User.employee_number == employee_number).first()
        )
        if existing_employee:
            raise ValueError("Ce numéro d'employé existe déjà")

        # Créer l'utilisateur avec le mot de passe haché
        user = User(
            employee_number=employee_number,
            full_name=full_name,
            email=email.lower(),
            password_hash=hash_password(password),
            role=role,
            is_active=True,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return user


def authenticate_user(email: str, password: str) -> Tuple[User, str]:
    """
    Authentifie un utilisateur et retourne un token JWT.

    Args:
        email: Email de l'utilisateur
        password: Mot de passe en clair

    Returns:
        Tuple (utilisateur, token JWT)

    Raises:
        AuthenticationError: Si les identifiants sont invalides
    """
    with get_db() as db:
        # Rechercher l'utilisateur par email
        user = db.query(User).filter(User.email == email.lower()).first()

        if not user:
            raise AuthenticationError("Email ou mot de passe incorrect")

        if not user.is_active:
            raise AuthenticationError("Ce compte a été désactivé")

        # Vérifier le mot de passe
        if not verify_password(password, user.password_hash):
            raise AuthenticationError("Email ou mot de passe incorrect")

        # Générer le token JWT
        token = create_access_token(
            user_id=user.id, employee_number=user.employee_number, role=user.role.value
        )

        # Sauvegarder le token localement pour persistance
        save_token(token)

        return user, token


def get_current_user(db: Session, token: str) -> Optional[User]:
    """
    Récupère l'utilisateur courant à partir du token JWT.

    Args:
        db: Session de base de données
        token: Token JWT

    Returns:
        L'utilisateur ou None si token invalide
    """
    payload = decode_access_token(token)

    if not payload:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    user = db.query(User).filter(User.id == user_id).first()

    if user and not user.is_active:
        return None

    return user


def change_password(
    db: Session, user: User, old_password: str, new_password: str
) -> bool:
    """
    Change le mot de passe d'un utilisateur.

    Args:
        db: Session de base de données
        user: L'utilisateur
        old_password: Ancien mot de passe
        new_password: Nouveau mot de passe

    Returns:
        True si le changement a réussi

    Raises:
        AuthenticationError: Si l'ancien mot de passe est incorrect
    """
    if not verify_password(old_password, user.password_hash):
        raise AuthenticationError("Mot de passe actuel incorrect")

    user.password_hash = hash_password(new_password)
    db.commit()

    return True


def get_authenticated_user(db: Session) -> User:
    """
    Récupère l'utilisateur authentifié à partir du token stocké.

    Cette fonction vérifie automatiquement :
    - Si un token existe
    - Si le token est valide et non expiré
    - Si l'utilisateur existe et est actif

    Args:
        db: Session de base de données

    Returns:
        L'utilisateur authentifié

    Raises:
        AuthenticationError: Si l'utilisateur n'est pas authentifié
    """
    token, error = get_valid_token()

    if error == "not_found":
        raise AuthenticationError("Veuillez vous connecter")
    elif error == "expired":
        raise AuthenticationError("Session expirée, veuillez vous reconnecter")
    elif error == "invalid":
        raise AuthenticationError("Session invalide, veuillez vous reconnecter")

    user = get_current_user(db, token)

    if not user:
        clear_token()
        raise AuthenticationError("Utilisateur introuvable, veuillez vous reconnecter")

    return user


def create_user(
    employee_number: str,
    full_name: str,
    email: str,
    password: str,
    role: RoleEnum,
) -> User:
    """
    Crée un nouveau collaborateur (management uniquement).

    Args:
        employee_number: Numéro d'employé
        full_name: Nom complet
        email: Email
        password: Mot de passe
        role: Rôle du collaborateur

    Returns:
        Le collaborateur créé

    Raises:
        AuthenticationError: Si non authentifié
        ValueError: Si permission refusée ou données invalides
    """
    with get_db() as db:
        current_user = get_authenticated_user(db)

        # Vérifier les permissions
        if current_user.role != RoleEnum.MANAGEMENT:
            raise ValueError("Seul le management peut créer des collaborateurs")

        # Validation des données
        if not employee_number or not employee_number.strip():
            raise ValueError("Le numéro d'employé est obligatoire")

        if not full_name or not full_name.strip():
            raise ValueError("Le nom complet est obligatoire")

        if not email or not email.strip() or "@" not in email:
            raise ValueError("L'email est invalide")

        if not password or len(password) < 8:
            raise ValueError("Le mot de passe doit contenir au moins 8 caractères")

        # Vérifier unicité
        if db.query(User).filter(User.employee_number == employee_number).first():
            raise ValueError("Ce numéro d'employé existe déjà")

        if db.query(User).filter(User.email == email).first():
            raise ValueError("Cet email est déjà utilisé")

        # Créer l'utilisateur avec le mot de passe haché
        new_user = User(
            employee_number=employee_number,
            full_name=full_name,
            email=email.lower(),
            password_hash=hash_password(password),
            role=role,
            is_active=True,
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Journaliser la création
        log_user_creation(
            user_email=new_user.email,
            created_by=current_user.email,
            role=role.value
        )

        # Access full_name before leaving the session
        user_name = new_user.full_name
        user_id = new_user.id

        return new_user


def get_all_users() -> list:
    """
    Récupère tous les utilisateurs (nécessite authentification).
        
    Returns:
        Liste de tous les utilisateurs
        
    Raises:
        AuthenticationError: Si non authentifié
    """
    with get_db() as db:
        get_authenticated_user(db)
        return db.query(User).all()


def update_user(
    employee_number: str,
    new_employee_number: str = None,
    full_name: str = None,
    email: str = None,
    role: RoleEnum = None,
    is_active: bool = None,
) -> User:
    """
    Modifie un collaborateur (management uniquement).

    Args:
        employee_number: Numéro d'employé du collaborateur à modifier
        new_employee_number: Nouveau numéro d'employé
        full_name: Nouveau nom
        email: Nouvel email
        role: Nouveau rôle (département)
        is_active: Nouveau statut actif

    Returns:
        Le collaborateur modifié

    Raises:
        AuthenticationError: Si non authentifié
        ValueError: Si permission refusée ou données invalides
    """
    with get_db() as db:
        current_user = get_authenticated_user(db)
        
        # Vérifier les permissions
        if current_user.role != RoleEnum.MANAGEMENT:
            raise ValueError("Seul le management peut modifier des collaborateurs")

        # Trouver l'utilisateur par employee_number
        user = db.query(User).filter(User.employee_number == employee_number).first()
        if not user:
            raise ValueError(f"Utilisateur avec le numero {employee_number} non trouve")

        # Tracer les changements pour la journalisation
        changes = {}

        # Validation et application des modifications
        if new_employee_number is not None:
            if not new_employee_number.strip():
                raise ValueError("Le numéro d'employé ne peut pas être vide")

            existing = (
                db.query(User)
                .filter(User.employee_number == new_employee_number, User.id != user.id)
                .first()
            )
            if existing:
                raise ValueError("Ce numéro d'employé est déjà utilisé")

            changes["employee_number"] = {"old": user.employee_number, "new": new_employee_number}
            user.employee_number = new_employee_number

        if full_name is not None:
            if not full_name.strip():
                raise ValueError("Le nom complet ne peut pas être vide")
            changes["full_name"] = {"old": user.full_name, "new": full_name}
            user.full_name = full_name

        if email is not None:
            if not email.strip() or "@" not in email:
                raise ValueError("L'email est invalide")

            existing = (
                db.query(User).filter(User.email == email, User.id != user.id).first()
            )
            if existing:
                raise ValueError("Cet email est déjà utilisé")

            changes["email"] = {"old": user.email, "new": email}
            user.email = email

        if role is not None:
            changes["role"] = {"old": user.role.value, "new": role.value}
            user.role = role

        if is_active is not None:
            changes["is_active"] = {"old": user.is_active, "new": is_active}
            user.is_active = is_active

        db.commit()
        db.refresh(user)

        # Journaliser la modification
        if changes:
            log_user_update(
                user_email=user.email,
                updated_by=current_user.email,
                changes=changes
            )

        return user


def delete_user(employee_number: str) -> bool:
    """
    Supprime un collaborateur (management uniquement).
    
    Args:
        employee_number: Numéro d'employé du collaborateur à supprimer
        
    Returns:
        True si la suppression a réussi
        
    Raises:
        AuthenticationError: Si non authentifié
        ValueError: Si permission refusée ou utilisateur non trouvé
    """
    with get_db() as db:
        current_user = get_authenticated_user(db)
        
        # Vérifier les permissions
        if current_user.role != RoleEnum.MANAGEMENT:
            raise ValueError("Seul le management peut supprimer des collaborateurs")
        
        # Trouver l'utilisateur par employee_number
        user = db.query(User).filter(User.employee_number == employee_number).first()
        if not user:
            raise ValueError(f"Utilisateur avec le numero {employee_number} non trouve")
        
        # Empêcher de se supprimer soi-même
        if user.id == current_user.id:
            raise ValueError("Vous ne pouvez pas supprimer votre propre compte")
        
        db.delete(user)
        db.commit()
        
        return True
