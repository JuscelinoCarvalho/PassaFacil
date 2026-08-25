from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.core.config import settings
from app.db.session import get_db
from app.models import SubscriptionPlan, SubscriptionStatus, User

DbSession = Annotated[Session, Depends(get_db)]
bearer = HTTPBearer(auto_error=False)


def get_owner_user(db: DbSession) -> User:
    user = db.scalar(select(User).where(User.email == settings.owner_email))
    if not user:
        raise HTTPException(status_code=503, detail="Usuário proprietário ainda não foi inicializado")
    return user


def get_current_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> User:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Autenticação necessária")
    try:
        user_id = UUID(decode_access_token(credentials.credentials))
    except (jwt.PyJWTError, ValueError, KeyError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido") from None
    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário inválido")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_admin_user(user: CurrentUser) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso restrito ao administrador")
    return user


AdminUser = Annotated[User, Depends(get_admin_user)]

PAID_PLANS = {SubscriptionPlan.plus, SubscriptionPlan.pro}


def user_has_access(user: User) -> bool:
    # Acesso gratuito temporário (sistema em evolução): libera todo mundo sem
    # cobrar. Reversível — desligar FREE_ACCESS no /etc restaura o paywall. O
    # código de pagamento (Asaas/checkout) segue intacto, só fica oculto.
    if settings.free_access:
        return True
    if user.is_admin:
        return True
    sub = user.subscription
    if not (
        sub
        and sub.plan in PAID_PLANS
        and sub.status in {SubscriptionStatus.active, SubscriptionStatus.trialing}
    ):
        return False
    # current_period_end None = acesso sem prazo (concessões antigas/admin); caso
    # contrário, o acesso vale até a data de expiração (pagamento = 2 anos).
    end = sub.current_period_end
    if end is None:
        return True
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    return end >= datetime.now(timezone.utc)


def pending_conversion(user: User) -> dict | None:
    """Conversão Google Ads pendente (pagamento confirmado ainda não enviado ao
    Google). Só existe para pagamentos reais — admin/concessões antigas nunca
    setam a flag. Consumido por /auth/me e /billing/status."""
    sub = user.subscription
    if sub and sub.conversion_pending and not sub.conversion_reported:
        return {
            "transaction_id": sub.provider_subscription_id or "",
            "value": settings.price_reais,
            "currency": "BRL",
        }
    return None


def get_paid_user(user: CurrentUser) -> User:
    if not user.is_admin and not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Confirme seu e-mail para ativar a conta. Verifique sua caixa de entrada.",
        )
    if not user_has_access(user):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Acesso exclusivo para assinantes. Faça o teste grátis ou libere o acesso completo.",
        )
    return user


PaidUser = Annotated[User, Depends(get_paid_user)]
