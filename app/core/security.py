from datetime import datetime, timedelta
from typing import Optional, Any
from jose import jwt, JWTError
from passlib.context import CryptContext

# --- Configuration et Constantes ---

# Remplacez ceci par une clé secrète forte provenant de vos variables d'environnement (.env)
# NE PAS LAISSER CELA EN DUR EN PRODUCTION !
SECRET_KEY = "VOTRE_SECRET_KEY_A_METTRE_DANS_LE_ENV" 
ALGORITHM = "HS256"
# Durée de validité du jeton d'accès (ex: 60 minutes)
ACCESS_TOKEN_EXPIRE_MINUTES = 60 

# Contexte pour le hachage des mots de passe
# bcrypt est l'algorithme recommandé
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- 1. Gestion des Mots de Passe ---

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Vérifie si le mot de passe simple correspond au hachage stocké.
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Retourne le hachage sécurisé du mot de passe.
    """
    return pwd_context.hash(password)

# --- 2. Gestion des Jetons JWT ---

def create_access_token(
    subject: str | Any, 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Crée un jeton JWT d'accès pour un utilisateur (subject).
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # Utilise la durée par défaut si aucune n'est spécifiée
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- 3. Décodage du Jetons JWT (Optionnel mais Utile) ---

def decode_access_token(token: str) -> Optional[str]:
    """
    Décode et valide le jeton JWT.
    Retourne le 'subject' (ID utilisateur) ou None en cas d'erreur/expiration.
    """
    try:
        payload = jwt.decode(
            token, 
            SECRET_KEY, 
            algorithms=[ALGORITHM]
        )
        # Le 'sub' (subject) est ce qui a été encodé comme identifiant unique
        return payload.get("sub")
    except JWTError:
        # Le jeton est invalide ou a expiré
        return None
