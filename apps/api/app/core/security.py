from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.core.config import settings

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, encoded: str) -> bool:
    return password_hash.verify(password, encoded)


def create_access_token(subject: str) -> str:
    expires = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode({"sub": subject, "exp": expires}, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str:
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    return str(payload["sub"])


def create_email_verification_token(subject: str) -> str:
    expires = datetime.now(UTC) + timedelta(hours=settings.email_verify_token_hours)
    return jwt.encode(
        {"sub": subject, "purpose": "email_verify", "exp": expires},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def decode_email_verification_token(token: str) -> str:
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    if payload.get("purpose") != "email_verify":
        raise jwt.InvalidTokenError("purpose inválido")
    return str(payload["sub"])


def create_password_reset_token(subject: str) -> str:
    expires = datetime.now(UTC) + timedelta(hours=1)
    return jwt.encode(
        {"sub": subject, "purpose": "password_reset", "exp": expires},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def decode_password_reset_token(token: str) -> str:
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    if payload.get("purpose") != "password_reset":
        raise jwt.InvalidTokenError("purpose inválido")
    return str(payload["sub"])

