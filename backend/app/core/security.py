"""Hash de contrasenas y emision/validacion de JWT.

- Contrasenas: PBKDF2-HMAC-SHA256 con sal aleatoria (biblioteca estandar).
- Tokens: JWT firmados con HS256 mediante PyJWT.

El secreto y la expiracion se configuran por entorno (`JWT_SECRET`,
`JWT_ACCESS_TOKEN_EXPIRE_MINUTES`). En desarrollo hay un secreto por defecto;
en produccion debe definirse uno propio.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import get_settings

_ALGORITHM = "pbkdf2_sha256"
_ITERATIONS = 200_000
_SALT_BYTES = 16


def hash_password(password: str) -> str:
    salt = secrets.token_hex(_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), _ITERATIONS)
    return f"{_ALGORITHM}${_ITERATIONS}${salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, iterations, salt, digest = stored.split("$")
    except ValueError:
        return False
    if algorithm != _ALGORITHM:
        return False
    candidate = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), int(iterations)
    )
    return hmac.compare_digest(candidate.hex(), digest)


def create_access_token(subject: str | int, extra: dict | None = None) -> tuple[str, datetime]:
    """Devuelve (token, fecha_de_expiracion)."""
    settings = get_settings()
    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    payload = {
        "sub": str(subject),
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
        **(extra or {}),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, expires_at


def decode_token(token: str) -> dict:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:  # expirado, firma invalida, malformado...
        raise ValueError("Token invalido o expirado") from exc
