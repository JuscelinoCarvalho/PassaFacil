from typing import Annotated
from uuid import UUID

import jwt
from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.deps import DbSession
from app.core.security import decode_access_token
from app.models import Feedback, User
from app.schemas.feedback import FeedbackRequest, FeedbackResponse
from app.services.email import send_feedback_email

router = APIRouter(prefix="/feedback", tags=["feedback"])
_bearer = HTTPBearer(auto_error=False)


def get_optional_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User | None:
    """Igual ao get_current_user, mas nunca levanta 401 — o widget é público."""
    if not credentials:
        return None
    try:
        user_id = UUID(decode_access_token(credentials.credentials))
    except (jwt.PyJWTError, ValueError, KeyError):
        return None
    user = db.get(User, user_id)
    return user if user and user.is_active else None


OptionalUser = Annotated[User | None, Depends(get_optional_user)]


@router.post("", response_model=FeedbackResponse)
@router.post("/", response_model=FeedbackResponse, include_in_schema=False)
def submit_feedback(payload: FeedbackRequest, db: DbSession, user: OptionalUser) -> FeedbackResponse:
    """Recebe uma mensagem de ajuda/reclamação: grava no banco e avisa o suporte
    por e-mail. Público (funciona logado ou não)."""
    entry = Feedback(
        category=payload.category,
        message=payload.message.strip(),
        contact_email=payload.contact_email,
        page=payload.page,
        user_id=user.id if user else None,
        user_email=user.email if user else None,
    )
    db.add(entry)
    db.commit()

    # Best-effort: nunca falhar a resposta ao usuário por causa do e-mail.
    send_feedback_email(
        category=payload.category,
        message=entry.message,
        contact_email=payload.contact_email,
        user_email=user.email if user else None,
        page=payload.page,
    )
    return FeedbackResponse(ok=True)
