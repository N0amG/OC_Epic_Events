"""
Utilitaires de sécurité pour Epic Events CRM

Ce module fournit les fonctions pour :
- Hachage et vérification des mots de passe (bcrypt)
- Génération et validation des tokens JWT
- Stockage persistant du token (fichier local)
"""

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Tuple

import bcrypt
import jwt
from dotenv import load_dotenv

load_dotenv()

# Clé secrète pour signer les tokens JWT (à définir dans .env)
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24  # Durée de validité du token (1 jour)

# Chemin du fichier de stockage du token
TOKEN_FILE = Path(__file__).parent.parent / ".epic_token"


# ============================================================
# HACHAGE DES MOTS DE PASSE (bcrypt)
# ============================================================

def hash_password(password: str) -> str:
    """
    Hache un mot de passe avec bcrypt.
    
    bcrypt génère automatiquement un sel aléatoire et l'intègre
    dans le hash final. Pas besoin de stocker le sel séparément.
    
    Args:
        password: Le mot de passe en clair
        
    Returns:
        Le hash du mot de passe (str)
    """
    # Encode le mot de passe en bytes
    password_bytes = password.encode('utf-8')
    # Génère le sel et hache (cost factor = 12 par défaut)
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    # Retourne le hash en string pour stockage en BDD
    return hashed.decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """
    Vérifie si un mot de passe correspond à son hash.
    
    Args:
        password: Le mot de passe en clair à vérifier
        password_hash: Le hash stocké en base de données
        
    Returns:
        True si le mot de passe est correct, False sinon
    """
    password_bytes = password.encode('utf-8')
    hash_bytes = password_hash.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hash_bytes)


# ============================================================
# GESTION DES TOKENS JWT
# ============================================================

def create_access_token(user_id: int, employee_number: str, role: str) -> str:
    """
    Crée un token JWT pour un utilisateur authentifié.
    
    Le token contient :
    - sub: l'ID de l'utilisateur
    - employee_number: le numéro d'employé
    - role: le rôle de l'utilisateur
    - exp: la date d'expiration
    - iat: la date de création
    
    Args:
        user_id: L'ID de l'utilisateur
        employee_number: Le numéro d'employé
        role: Le rôle de l'utilisateur
        
    Returns:
        Le token JWT encodé (str)
    """
    now = datetime.now(timezone.utc)  # Timezone-aware UTC
    payload = {
        "sub": str(user_id),  # JWT requiert une string pour "sub"
        "employee_number": employee_number,
        "role": role,
        "iat": now,
        "exp": now + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """
    Décode et valide un token JWT.
    
    Args:
        token: Le token JWT à décoder
        
    Returns:
        Le payload du token si valide, None sinon
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        # Token expiré
        return None
    except jwt.InvalidTokenError:
        # Token invalide
        return None


def get_token_user_id(token: str) -> Optional[int]:
    """
    Extrait l'ID utilisateur d'un token JWT.
    
    Args:
        token: Le token JWT
        
    Returns:
        L'ID de l'utilisateur ou None si token invalide
    """
    payload = decode_access_token(token)
    if payload and payload.get("sub"):
        return int(payload.get("sub"))
    return None


def get_token_role(token: str) -> Optional[str]:
    """
    Extrait le rôle de l'utilisateur d'un token JWT.
    
    Args:
        token: Le token JWT
        
    Returns:
        Le rôle de l'utilisateur ou None si token invalide
    """
    payload = decode_access_token(token)
    if payload:
        return payload.get("role")
    return None


# ============================================================
# STOCKAGE PERSISTANT DU TOKEN
# ============================================================

def save_token(token: str) -> None:
    """
    Sauvegarde le token JWT dans un fichier local.
    
    Args:
        token: Le token JWT à sauvegarder
    """
    TOKEN_FILE.write_text(token, encoding="utf-8")


def load_token() -> Optional[str]:
    """
    Charge le token JWT depuis le fichier local.
    
    Returns:
        Le token JWT ou None si non trouvé
    """
    if TOKEN_FILE.exists():
        token = TOKEN_FILE.read_text(encoding="utf-8").strip()
        return token if token else None
    return None


def clear_token() -> None:
    """
    Vide le token JWT (déconnexion).
    Le fichier est conservé mais vidé.
    """
    TOKEN_FILE.write_text("", encoding="utf-8")


def is_token_expired(token: str) -> bool:
    """
    Vérifie si un token est expiré.
    
    Args:
        token: Le token JWT
        
    Returns:
        True si le token est expiré, False sinon
    """
    try:
        jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return False
    except jwt.ExpiredSignatureError:
        return True
    except jwt.InvalidTokenError:
        return True


def get_valid_token() -> Tuple[Optional[str], Optional[str]]:
    """
    Récupère le token stocké et vérifie sa validité.
    
    Returns:
        Tuple (token, erreur):
        - (token, None) si le token est valide
        - (None, "expired") si le token est expiré
        - (None, "not_found") si aucun token n'existe
        - (None, "invalid") si le token est invalide
    """
    token = load_token()
    
    if not token:
        return None, "not_found"
    
    try:
        jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return token, None
    except jwt.ExpiredSignatureError:
        # Token expiré → on le supprime et on informe
        clear_token()
        return None, "expired"
    except jwt.InvalidTokenError:
        # Token invalide → on le supprime
        clear_token()
        return None, "invalid"
