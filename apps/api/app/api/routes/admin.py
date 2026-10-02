from datetime import datetime, timezone

from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import AdminUser, DbSession
from app.models import SubscriptionPlan, User

router = APIRouter(prefix="/admin", tags=["admin"])

# Janela para considerar um usuário "online": último sinal de atividade recente.
ONLINE_WINDOW_SECONDS = 300


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


@router.get("/users")
def list_users(_: AdminUser, db: DbSession) -> dict:
    """Painel do admin: usuários da base com data de criação, último acesso,
    quantidade de acessos e status online/offline."""
    now = datetime.now(timezone.utc)
    users = db.scalars(select(User).order_by(User.created_at.desc())).all()

    rows = []
    online_count = 0
    for u in users:
        last = u.last_seen_at
        if last is not None and last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        is_online = last is not None and (now - last).total_seconds() <= ONLINE_WINDOW_SECONDS
        if is_online:
            online_count += 1
        rows.append(
            {
                "id": str(u.id),
                "email": u.email,
                "full_name": u.full_name,
                "is_admin": u.is_admin,
                "email_verified": u.email_verified,
                "is_active": u.is_active,
                "plan": u.subscription.plan.value if u.subscription else SubscriptionPlan.free.value,
                "created_at": _iso(u.created_at),
                "last_seen_at": _iso(last),
                "access_count": u.access_count or 0,
                "is_online": is_online,
            }
        )

    return {
        "total": len(rows),
        "online": online_count,
        "online_window_seconds": ONLINE_WINDOW_SECONDS,
        "users": rows,
    }
