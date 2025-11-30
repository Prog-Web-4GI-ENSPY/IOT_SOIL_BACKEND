import pytest
from datetime import datetime, timedelta
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token
)
from app.core.config import settings


class TestPasswordHashing:
    """Tests pour le hashing des mots de passe"""

    def test_password_hash(self):
        """Test que le mot de passe est correctement hashé"""
        password = "TestPassword123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert len(hashed) > 0

    def test_password_verification_success(self):
        """Test de vérification d'un mot de passe correct"""
        password = "TestPassword123"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_password_verification_failure(self):
        """Test de vérification d'un mot de passe incorrect"""
        password = "TestPassword123"
        wrong_password = "WrongPassword456"
        hashed = get_password_hash(password)

        assert verify_password(wrong_password, hashed) is False

    def test_different_hashes_for_same_password(self):
        """Test que le même mot de passe produit des hashs différents"""
        password = "TestPassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        assert hash1 != hash2
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestTokenCreation:
    """Tests pour la création de tokens"""

    def test_create_access_token(self):
        """Test de création d'un token d'accès"""
        data = {"sub": "user123", "email": "test@example.com"}
        token = create_access_token(data)

        assert token is not None
        assert len(token) > 0

    def test_create_refresh_token(self):
        """Test de création d'un token de rafraîchissement"""
        data = {"sub": "user123", "email": "test@example.com"}
        token = create_refresh_token(data)

        assert token is not None
        assert len(token) > 0

    def test_access_token_contains_correct_data(self):
        """Test que le token d'accès contient les bonnes données"""
        data = {"sub": "user123", "email": "test@example.com", "role": "user"}
        token = create_access_token(data)
        payload = decode_token(token)

        assert payload is not None
        assert payload["sub"] == "user123"
        assert payload["email"] == "test@example.com"
        assert payload["role"] == "user"
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload

    def test_refresh_token_contains_correct_data(self):
        """Test que le token de rafraîchissement contient les bonnes données"""
        data = {"sub": "user123", "email": "test@example.com"}
        token = create_refresh_token(data)
        payload = decode_token(token)

        assert payload is not None
        assert payload["sub"] == "user123"
        assert payload["email"] == "test@example.com"
        assert payload["type"] == "refresh"
        assert "exp" in payload
        assert "iat" in payload

    def test_access_token_expiration(self):
        """Test que le token d'accès a la bonne expiration"""
        data = {"sub": "user123"}
        token = create_access_token(data)
        payload = decode_token(token)

        exp = datetime.fromtimestamp(payload["exp"])
        iat = datetime.fromtimestamp(payload["iat"])

        expected_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        actual_delta = exp - iat

        assert abs((actual_delta - expected_delta).total_seconds()) < 2

    def test_refresh_token_expiration(self):
        """Test que le token de rafraîchissement a la bonne expiration"""
        data = {"sub": "user123"}
        token = create_refresh_token(data)
        payload = decode_token(token)

        exp = datetime.fromtimestamp(payload["exp"])
        iat = datetime.fromtimestamp(payload["iat"])

        expected_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        actual_delta = exp - iat

        assert abs((actual_delta - expected_delta).total_seconds()) < 2

    def test_custom_expiration(self):
        """Test de création d'un token avec expiration personnalisée"""
        data = {"sub": "user123"}
        custom_delta = timedelta(minutes=15)
        token = create_access_token(data, expires_delta=custom_delta)
        payload = decode_token(token)

        exp = datetime.fromtimestamp(payload["exp"])
        iat = datetime.fromtimestamp(payload["iat"])
        actual_delta = exp - iat

        assert abs((actual_delta - custom_delta).total_seconds()) < 2


class TestTokenDecoding:
    """Tests pour le décodage de tokens"""

    def test_decode_valid_token(self):
        """Test de décodage d'un token valide"""
        data = {"sub": "user123", "email": "test@example.com"}
        token = create_access_token(data)
        payload = decode_token(token)

        assert payload is not None
        assert payload["sub"] == "user123"
        assert payload["email"] == "test@example.com"

    def test_decode_invalid_token(self):
        """Test de décodage d'un token invalide"""
        invalid_token = "invalid.token.here"
        payload = decode_token(invalid_token)

        assert payload is None

    def test_decode_malformed_token(self):
        """Test de décodage d'un token mal formé"""
        malformed_token = "notavalidtoken"
        payload = decode_token(malformed_token)

        assert payload is None


class TestTokenVerification:
    """Tests pour la vérification de tokens"""

    def test_verify_valid_access_token(self):
        """Test de vérification d'un token d'accès valide"""
        data = {"sub": "user123", "email": "test@example.com"}
        token = create_access_token(data)
        payload = verify_token(token, token_type="access")

        assert payload is not None
        assert payload["sub"] == "user123"
        assert payload["type"] == "access"

    def test_verify_valid_refresh_token(self):
        """Test de vérification d'un token de rafraîchissement valide"""
        data = {"sub": "user123", "email": "test@example.com"}
        token = create_refresh_token(data)
        payload = verify_token(token, token_type="refresh")

        assert payload is not None
        assert payload["sub"] == "user123"
        assert payload["type"] == "refresh"

    def test_verify_wrong_token_type(self):
        """Test de vérification d'un token avec le mauvais type"""
        data = {"sub": "user123"}
        access_token = create_access_token(data)

        payload = verify_token(access_token, token_type="refresh")
        assert payload is None

    def test_verify_invalid_token(self):
        """Test de vérification d'un token invalide"""
        payload = verify_token("invalid.token", token_type="access")
        assert payload is None

    def test_verify_expired_token(self):
        """Test de vérification d'un token expiré"""
        data = {"sub": "user123"}
        expired_delta = timedelta(seconds=-1)
        token = create_access_token(data, expires_delta=expired_delta)

        import time
        time.sleep(2)

        payload = verify_token(token, token_type="access")
        assert payload is None
