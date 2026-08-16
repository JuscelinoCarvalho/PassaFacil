import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, parseaddr

from app.core.config import settings

logger = logging.getLogger("passafacil.email")


def _send(
    to_email: str | list[str],
    subject: str,
    html: str,
    reply_to: str | None = None,
    bcc: list[str] | None = None,
) -> bool:
    to_list = [to_email] if isinstance(to_email, str) else list(to_email)
    bcc_list = bcc or []
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    # Codifica só o nome de exibição (acentos) e mantém o endereço puro/qualificado,
    # senão o exim rejeita o header From como "unqualified address".
    name, addr = parseaddr(settings.smtp_from)
    msg["From"] = formataddr((name, addr)) if name else addr
    msg["To"] = ", ".join(to_list)
    # Bcc: send_message entrega às cópias ocultas e remove o cabeçalho antes de enviar.
    if bcc_list:
        msg["Bcc"] = ", ".join(bcc_list)
    if reply_to:
        _, reply_addr = parseaddr(reply_to)
        if reply_addr:
            msg["Reply-To"] = reply_addr
    msg.attach(MIMEText(html, "html", "utf-8"))
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
            if settings.smtp_tls:
                server.starttls()
            if settings.smtp_user:
                server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)
        return True
    except Exception:  # noqa: BLE001 - não derrubar o cadastro por falha de e-mail
        logger.exception("Falha ao enviar e-mail para %s", to_email)
        return False


def send_verification_email(to_email: str, full_name: str, token: str) -> bool:
    link = f"{settings.site_url}/api/v1/auth/verify?token={token}"
    first_name = (full_name or "").strip().split(" ")[0] or "Olá"
    html = f"""
    <div style="font-family: Arial, Helvetica, sans-serif; max-width: 520px; margin: 0 auto; color: #1e293b;">
      <h2 style="color: #7c3aed; margin-bottom: 4px;">Passa Fácil</h2>
      <p>Olá, {first_name}! Falta um passo para ativar sua conta.</p>
      <p>Confirme seu e-mail clicando no botão abaixo:</p>
      <p style="text-align: center; margin: 28px 0;">
        <a href="{link}" style="background: #7c3aed; color: #fff; text-decoration: none;
           padding: 14px 28px; border-radius: 8px; font-weight: bold; display: inline-block;">
          Ativar minha conta
        </a>
      </p>
      <p style="font-size: 13px; color: #64748b;">
        Se o botão não funcionar, copie e cole este link no navegador:<br>
        <a href="{link}">{link}</a>
      </p>
      <p style="font-size: 12px; color: #94a3b8; margin-top: 24px;">
        O link expira em {settings.email_verify_token_hours} horas.
        Se você não criou uma conta no Passa Fácil, ignore este e-mail.
      </p>
    </div>
    """
    return _send(to_email, "Ative sua conta no Passa Fácil", html)


_FEEDBACK_LABELS = {
    "ajuda": "Pedido de ajuda",
    "reclamacao": "Reclamação",
    "sugestao": "Sugestão",
    "elogio": "Elogio",
    "outro": "Contato",
}


def send_feedback_email(
    category: str,
    message: str,
    contact_email: str | None,
    user_email: str | None,
    page: str | None,
) -> bool:
    """Envia ao suporte a mensagem do widget 'Fale conosco'."""
    label = _FEEDBACK_LABELS.get(category, "Contato")
    reply_to = contact_email or user_email or "(não informado)"
    origin = "Usuário logado" if user_email else "Visitante"
    safe_message = (message or "").replace("\n", "<br>")
    html = f"""
    <div style="font-family: Arial, Helvetica, sans-serif; max-width: 560px; margin: 0 auto; color: #1e293b;">
      <h2 style="color: #7c3aed; margin-bottom: 4px;">Passa Fácil · {label}</h2>
      <table style="font-size: 14px; color: #334155; margin: 12px 0;">
        <tr><td style="padding: 2px 12px 2px 0; color:#64748b;">Categoria</td><td><b>{label}</b></td></tr>
        <tr><td style="padding: 2px 12px 2px 0; color:#64748b;">Responder para</td><td>{reply_to}</td></tr>
        <tr><td style="padding: 2px 12px 2px 0; color:#64748b;">Origem</td><td>{origin}{f" ({user_email})" if user_email else ""}</td></tr>
        <tr><td style="padding: 2px 12px 2px 0; color:#64748b;">Página</td><td>{page or "—"}</td></tr>
      </table>
      <div style="background:#f8fafc; border-left:3px solid #7c3aed; padding:12px 16px; border-radius:6px; font-size:15px; line-height:1.5;">
        {safe_message}
      </div>
    </div>
    """
    return _send(
        settings.support_to_list,
        f"[Passa Fácil] {label}",
        html,
        reply_to=contact_email or user_email,
        bcc=settings.support_bcc_list,
    )


def send_password_reset_email(to_email: str, full_name: str, token: str) -> bool:
    link = f"{settings.site_url}/api/v1/auth/reset?token={token}"
    first_name = (full_name or "").strip().split(" ")[0] or "Olá"
    html = f"""
    <div style="font-family: Arial, Helvetica, sans-serif; max-width: 520px; margin: 0 auto; color: #1e293b;">
      <h2 style="color: #7c3aed; margin-bottom: 4px;">Passa Fácil</h2>
      <p>Olá, {first_name}! Recebemos um pedido para redefinir sua senha.</p>
      <p>Clique no botão abaixo para criar uma nova senha:</p>
      <p style="text-align: center; margin: 28px 0;">
        <a href="{link}" style="background: #7c3aed; color: #fff; text-decoration: none;
           padding: 14px 28px; border-radius: 8px; font-weight: bold; display: inline-block;">
          Redefinir minha senha
        </a>
      </p>
      <p style="font-size: 13px; color: #64748b;">
        Se o botão não funcionar, copie e cole este link no navegador:<br>
        <a href="{link}">{link}</a>
      </p>
      <p style="font-size: 12px; color: #94a3b8; margin-top: 24px;">
        O link expira em 1 hora. Se você não pediu para redefinir a senha, ignore este e-mail —
        sua senha atual continua valendo.
      </p>
    </div>
    """
    return _send(to_email, "Redefinir sua senha · Passa Fácil", html)
