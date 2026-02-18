"""
Contrôleur User pour Epic Events CRM

Ce module gère les opérations CRUD sur les collaborateurs.
Les fonctions d'authentification restent dans auth_controller.
"""

from typing import List
from epicevents.models import User, RoleEnum
from epicevents.sentry_config import log_user_creation, log_user_update
from epicevents.database import get_db
from epicevents.utils import hash_password
from epicevents.controllers.auth_controller import get_authenticated_user, AuthenticationError


def get_all_users() -> List[dict]:
    """
    Récupère tous les utilisateurs sous forme de dicts prêts à l'affichage.

    Returns:
        Liste de dicts utilisateurs

    Raises:
        AuthenticationError: Si non authentifié
    """
    with get_db() as db:
        get_authenticated_user(db)
        users = db.query(User).all()
        return [
            {
                "id": u.id,
                "employee_number": u.employee_number,
                "full_name": u.full_name,
                "email": u.email,
                "role": u.role.value,
            }
            for u in users
        ]


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

        if current_user.role != RoleEnum.MANAGEMENT:
            raise ValueError("Seul le management peut créer des collaborateurs")

        if not employee_number or not employee_number.strip():
            raise ValueError("Le numéro d'employé est obligatoire")

        if not full_name or not full_name.strip():
            raise ValueError("Le nom complet est obligatoire")

        if not email or not email.strip() or "@" not in email:
            raise ValueError("L'email est invalide")

        if not password or len(password) < 8:
            raise ValueError("Le mot de passe doit contenir au moins 8 caractères")

        if db.query(User).filter(User.employee_number == employee_number).first():
            raise ValueError("Ce numéro d'employé existe déjà")

        if db.query(User).filter(User.email == email).first():
            raise ValueError("Cet email est déjà utilisé")

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

        log_user_creation(
            user_email=new_user.email,
            created_by=current_user.email,
            role=role.value,
        )

        return new_user


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
        role: Nouveau rôle
        is_active: Nouveau statut actif

    Returns:
        Le collaborateur modifié

    Raises:
        AuthenticationError: Si non authentifié
        ValueError: Si permission refusée ou données invalides
    """
    with get_db() as db:
        current_user = get_authenticated_user(db)

        if current_user.role != RoleEnum.MANAGEMENT:
            raise ValueError("Seul le management peut modifier des collaborateurs")

        user = db.query(User).filter(User.employee_number == employee_number).first()
        if not user:
            raise ValueError(f"Utilisateur avec le numero {employee_number} non trouve")

        changes = {}

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

        if changes:
            log_user_update(
                user_email=user.email,
                updated_by=current_user.email,
                changes=changes,
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

        if current_user.role != RoleEnum.MANAGEMENT:
            raise ValueError("Seul le management peut supprimer des collaborateurs")

        user = db.query(User).filter(User.employee_number == employee_number).first()
        if not user:
            raise ValueError(f"Utilisateur avec le numero {employee_number} non trouve")

        if user.id == current_user.id:
            raise ValueError("Vous ne pouvez pas supprimer votre propre compte")

        db.delete(user)
        db.commit()

        return True
