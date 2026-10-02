from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession, pending_conversion, user_has_access
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_email_verification_token,
    create_password_reset_token,
    decode_email_verification_token,
    decode_password_reset_token,
    hash_password,
    verify_password,
)
from app.models import Subscription, User
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
)
from app.services.email import send_password_reset_email, send_verification_email

router = APIRouter(prefix="/auth", tags=["auth"])


def _send_verification(user: User) -> None:
    token = create_email_verification_token(str(user.id))
    send_verification_email(user.email, user.full_name, token)


def _status_page(title: str, message: str, ok: bool) -> str:
    color = "#16a34a" if ok else "#dc2626"
    cta = (
        f'<a href="{settings.site_url}" style="background:#7c3aed;color:#fff;text-decoration:none;'
        'padding:12px 24px;border-radius:8px;font-weight:bold;display:inline-block;margin-top:20px;">'
        "Ir para o Passa Fácil</a>"
    )
    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title} · Passa Fácil</title></head>
    <body style="font-family:Arial,Helvetica,sans-serif;background:#f8fafc;margin:0;">
      <div style="max-width:480px;margin:80px auto;background:#fff;border-radius:16px;
           padding:40px;text-align:center;box-shadow:0 10px 30px rgba(0,0,0,.08);">
        <h1 style="color:{color};margin:0 0 12px;font-size:24px;">{title}</h1>
        <p style="color:#475569;font-size:16px;line-height:1.5;">{message}</p>
        {cta}
      </div>
    </body></html>"""


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: DbSession) -> TokenResponse:
    email = payload.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="E-mail já cadastrado")
    user = User(
        email=email,
        full_name=payload.full_name.strip(),
        password_hash=hash_password(payload.password),
        email_verified=False,
    )
    user.access_count = 1
    user.last_seen_at = datetime.now(timezone.utc)
    db.add(user)
    db.flush()
    gclid = (payload.gclid or "").strip()[:512] or None
    db.add(Subscription(user_id=user.id, gclid=gclid))
    db.commit()
    db.refresh(user)
    _send_verification(user)
    return TokenResponse(access_token=create_access_token(str(user.id)), user=user)


@router.get("/verify", response_class=HTMLResponse)
def verify(token: str, db: DbSession) -> HTMLResponse:
    try:
        user_id = UUID(decode_email_verification_token(token))
    except Exception:  # noqa: BLE001
        return HTMLResponse(
            _status_page(
                "Link inválido ou expirado",
                "Este link de ativação não é mais válido. Faça login no site e peça um novo e-mail de ativação.",
                ok=False,
            ),
            status_code=400,
        )
    user = db.get(User, user_id)
    if not user:
        return HTMLResponse(
            _status_page("Conta não encontrada", "Não localizamos essa conta.", ok=False),
            status_code=404,
        )
    if not user.email_verified:
        user.email_verified = True
        db.commit()
    return HTMLResponse(
        _status_page(
            "Conta ativada! ✅",
            "Seu e-mail foi confirmado. Agora é só entrar no Passa Fácil e começar a estudar.",
            ok=True,
        )
    )


@router.post("/resend-verification")
def resend_verification(payload: ResendVerificationRequest, db: DbSession) -> dict:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user and not user.email_verified:
        _send_verification(user)
    return {"detail": "Se a conta existir e ainda não estiver ativada, enviamos um novo link de ativação."}


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: DbSession) -> dict:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user:
        token = create_password_reset_token(str(user.id))
        send_password_reset_email(user.email, user.full_name, token)
    return {"detail": "Se houver uma conta com esse e-mail, enviamos um link para redefinir a senha."}


@router.get("/reset", response_class=HTMLResponse)
def reset_form(token: str) -> HTMLResponse:
    # Página com formulário de nova senha (self-contained, sem depender do front).
    return HTMLResponse(f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Redefinir senha · Passa Fácil</title></head>
    <body style="font-family:Arial,Helvetica,sans-serif;background:#f8fafc;margin:0;">
      <div style="max-width:420px;margin:70px auto;background:#fff;border-radius:16px;padding:36px;
           box-shadow:0 10px 30px rgba(0,0,0,.08);">
        <h1 style="color:#7c3aed;font-size:22px;margin:0 0 6px;">Nova senha</h1>
        <p style="color:#475569;font-size:14px;">Digite sua nova senha (mínimo 8 caracteres).</p>
        <input id="pw" type="password" placeholder="Nova senha" minlength="8"
          style="width:100%;box-sizing:border-box;padding:12px 14px;border:1px solid #d8dbe6;border-radius:10px;font-size:15px;margin:10px 0;">
        <input id="pw2" type="password" placeholder="Confirmar nova senha" minlength="8"
          style="width:100%;box-sizing:border-box;padding:12px 14px;border:1px solid #d8dbe6;border-radius:10px;font-size:15px;margin:0 0 14px;">
        <button id="btn" style="width:100%;background:#7c3aed;color:#fff;border:none;padding:13px;border-radius:10px;font-weight:bold;font-size:15px;cursor:pointer;">
          Salvar nova senha</button>
        <p id="msg" style="font-size:14px;margin-top:14px;text-align:center;"></p>
      </div>
      <script>
        var token = {token!r};
        document.getElementById('btn').onclick = async function() {{
          var pw = document.getElementById('pw').value, pw2 = document.getElementById('pw2').value;
          var msg = document.getElementById('msg');
          if (pw.length < 8) {{ msg.style.color='#dc2626'; msg.textContent='A senha precisa ter ao menos 8 caracteres.'; return; }}
          if (pw !== pw2) {{ msg.style.color='#dc2626'; msg.textContent='As senhas não conferem.'; return; }}
          var r = await fetch('{settings.site_url}/api/v1/auth/reset-password', {{
            method:'POST', headers:{{'Content-Type':'application/json'}},
            body: JSON.stringify({{token: token, password: pw}}) }});
          if (r.ok) {{ msg.style.color='#16a34a'; msg.innerHTML='Senha alterada! <a href="{settings.site_url}">Entrar agora</a>'; }}
          else {{ var d = await r.json().catch(function(){{return {{}};}}); msg.style.color='#dc2626';
                 msg.textContent = (d.detail||'Link inválido ou expirado. Peça um novo.'); }}
        }};
      </script>
    </body></html>""")


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: DbSession) -> dict:
    try:
        user_id = UUID(decode_password_reset_token(payload.token))
    except Exception:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="Link inválido ou expirado. Peça um novo.") from None
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    user.password_hash = hash_password(payload.password)
    db.commit()
    return {"detail": "Senha redefinida com sucesso."}


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: DbSession) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="E-mail ou senha inválidos")
    user.access_count = (user.access_count or 0) + 1
    user.last_seen_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return TokenResponse(access_token=create_access_token(str(user.id)), user=user)


@router.get("/me")
def me(user: CurrentUser) -> dict:
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "is_admin": user.is_admin,
        "email_verified": user.email_verified,
        "has_access": user_has_access(user),
        "plan": user.subscription.plan.value if user.subscription else "free",
        "conversion": pending_conversion(user),
    }
