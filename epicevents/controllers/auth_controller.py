"""
Contrôleur d'authentification pour Epic Events CRM

Ce module gère :
- L'inscription des collaborateurs
- La connexion (authentification)
- La vérification des sessions
"""

from typing import Optional, Tuple
from sqlalchemy.orm import Session

from epicevents.models import User, RoleEnum
from epicevents.utils import (
    hash_password, 
    verify_password, 
    create_access_token, 
    decode_access_token,
    save_token,
    clear_token,
    get_valid_token
)


class AuthenticationError(Exception):
    """Exception levée lors d'une erreur d'authentification"""
    pass


class AuthorizationError(Exception):
    """Exception levée lors d'une erreur d'autorisation"""
    pass


def register_user(
    db: Session,
    employee_number: str,
    full_name: str,
    email: str,
    password: str,
    role: RoleEnum
) -> User:
    """
    Inscrit un nouveau collaborateur.
    
    Args:
        db: Session de base de données
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
    # Vérifier si l'email existe déjà
    existing_email = db.query(User).filter(User.email == email.lower()).first()
    if existing_email:
        raise ValueError("Cette adresse email est déjà utilisée")
    
    # Vérifier si le numéro d'employé existe déjà
    existing_employee = db.query(User).filter(User.employee_number == employee_number).first()
    if existing_employee:
        raise ValueError("Ce numéro d'employé existe déjà")
    
    # Créer l'utilisateur avec le mot de passe haché
    user = User(
        employee_number=employee_number,
        full_name=full_name,
        email=email.lower(),
        password_hash=hash_password(password),
        role=role,
        is_active=True
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


def authenticate_user(db: Session, email: str, password: str) -> Tuple[User, str]:
    """
    Authentifie un utilisateur et retourne un token JWT.
    
    Args:
        db: Session de base de données
        email: Email de l'utilisateur
        password: Mot de passe en clair
        
    Returns:
        Tuple (utilisateur, token JWT)
        
    Raises:
        AuthenticationError: Si les identifiants sont invalides
    """
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
        user_id=user.id,
        employee_number=user.employee_number,
        role=user.role.value
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


def change_password(db: Session, user: User, old_password: str, new_password: str) -> bool:
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


def deactivate_user(db: Session, user: User) -> bool:
    """
    Désactive un compte utilisateur.
    
    Args:
        db: Session de base de données
        user: L'utilisateur à désactiver
        
    Returns:
        True si la désactivation a réussi
    """
    user.is_active = False
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
