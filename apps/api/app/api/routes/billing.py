import json
import re
from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request

from app.api.deps import CurrentUser, DbSession, pending_conversion, user_has_access
from app.core.config import settings
from app.models import Subscription, SubscriptionPlan, SubscriptionStatus, User
from app.schemas.auth import CheckoutRequest
from app.services import asaas, google_ads

router = APIRouter(prefix="/billing", tags=["billing"])


def _ensure_subscription(db: DbSession, user: User) -> Subscription:
    if user.subscription:
        return user.subscription
    sub = Subscription(user_id=user.id)
    db.add(sub)
    db.flush()
    return sub


ACCESS_DURATION_DAYS = 730  # 2 anos de acesso por pagamento único


def _maybe_upload_conversion(db: DbSession, sub: Subscription) -> None:
    """Envia a conversão "Compra" ao Google Ads pela API (server-side), sem depender
    do gtag no navegador do comprador. Best-effort: qualquer falha é registrada em
    conversion_upload_error e NÃO interrompe a liberação do acesso; nesse caso a
    flag conversion_pending permanece ligada e o disparo client-side (gtag) cobre
    como fallback. O orderId é o mesmo id de transação usado no front, então o
    Google deduplica se as duas vias dispararem para a mesma compra."""
    if sub.conversion_uploaded or not sub.gclid or not settings.google_ads_ready:
        return
    try:
        now = datetime.now(timezone.utc)
        google_ads.upload_click_conversion(
            gclid=sub.gclid,
            conversion_datetime=now.strftime("%Y-%m-%d %H:%M:%S+00:00"),
            value=settings.price_reais,
            currency="BRL",
            order_id=sub.provider_subscription_id or str(sub.id),
        )
    except google_ads.GoogleAdsError as error:
        sub.conversion_upload_error = str(error)[:1000]
        db.commit()
        return
    # Sucesso: dispensa o fallback client-side para não depender de dedupe.
    sub.conversion_uploaded = True
    sub.conversion_pending = False
    sub.conversion_reported = True
    sub.conversion_upload_error = None
    db.commit()


def _grant_access(db: DbSession, sub: Subscription) -> None:
    sub.plan = SubscriptionPlan.pro
    sub.status = SubscriptionStatus.active
    # Acesso por 2 anos a partir do pagamento (pagamento único).
    sub.current_period_end = datetime.now(timezone.utc) + timedelta(days=ACCESS_DURATION_DAYS)
    # Marca a conversão Google Ads para o front reportar. Idempotente: só liga
    # enquanto ainda não foi reportada (webhook + confirmação preguiçosa podem
    # chamar _grant_access para o mesmo pagamento).
    if not sub.conversion_reported:
        sub.conversion_pending = True
    db.commit()
    # Tenta a via server-side (se habilitada e com gclid); em caso de sucesso ela
    # limpa o pending para o front não redisparar.
    _maybe_upload_conversion(db, sub)


def _friendly_asaas_error(error: asaas.AsaasError) -> str:
    try:
        data = json.loads(error.body)
        errors = data.get("errors") or []
        if errors:
            return errors[0].get("description") or "Não foi possível gerar a cobrança."
    except Exception:  # noqa: BLE001
        pass
    return "Não foi possível gerar a cobrança. Tente novamente."


@router.post("/checkout")
def checkout(payload: CheckoutRequest, user: CurrentUser, db: DbSession) -> dict:
    if not user.is_admin and not user.email_verified:
        raise HTTPException(status_code=403, detail="Confirme seu e-mail antes de pagar.")
    if user_has_access(user):
        return {"already_active": True}

    cpf_cnpj = re.sub(r"\D", "", payload.cpf_cnpj)
    if len(cpf_cnpj) not in (11, 14):
        raise HTTPException(status_code=422, detail="Informe um CPF (11 dígitos) ou CNPJ (14 dígitos) válido.")

    sub = _ensure_subscription(db, user)
    # Captura/atualiza o gclid no momento do checkout (última janela antes de pagar);
    # se o cadastro foi orgânico e a volta veio de um anúncio, ainda pegamos aqui.
    gclid = (payload.gclid or "").strip()[:512]
    if gclid:
        sub.gclid = gclid
    try:
        if not sub.provider_customer_id:
            customer = asaas.create_customer(user.full_name, user.email, cpf_cnpj)
            sub.provider_customer_id = customer["id"]
            sub.provider = "asaas"
            db.commit()

        payment = asaas.create_pix_payment(
            customer_id=sub.provider_customer_id,
            value=settings.price_reais,
            description="Passa Fácil — acesso Especialidade TI (2 anos)",
            external_reference=str(user.id),
            due_date=(date.today() + timedelta(days=3)).isoformat(),
        )
        sub.provider_subscription_id = payment["id"]
        db.commit()
        qr = asaas.get_pix_qr(payment["id"])
    except asaas.AsaasError as error:
        raise HTTPException(status_code=400, detail=_friendly_asaas_error(error)) from None

    return {
        "payment_id": payment["id"],
        "value": settings.price_reais,
        "status": payment.get("status"),
        "qr_image": qr.get("encodedImage"),
        "copy_paste": qr.get("payload"),
        "expiration": qr.get("expirationDate"),
    }


@router.get("/status")
def status(user: CurrentUser, db: DbSession) -> dict:
    # Confirmação preguiçosa: se houver cobrança pendente, consulta o Asaas.
    if not user_has_access(user) and user.subscription and user.subscription.provider_subscription_id:
        try:
            payment = asaas.get_payment(user.subscription.provider_subscription_id)
            if payment.get("status") in asaas.PAID_STATUSES:
                _grant_access(db, user.subscription)
        except asaas.AsaasError:
            pass
    return {
        "has_access": user_has_access(user),
        "plan": user.subscription.plan.value if user.subscription else "free",
        "conversion": pending_conversion(user),
    }


@router.post("/conversion/reported")
def conversion_reported(user: CurrentUser, db: DbSession) -> dict:
    """O front chama após disparar o gtag de conversão (Google Ads), para não
    reenviar. Deduplicado também pelo transaction_id no lado do Google."""
    sub = user.subscription
    if sub and sub.conversion_pending:
        sub.conversion_pending = False
        sub.conversion_reported = True
        db.commit()
    return {"ok": True}


@router.post("/webhook/asaas")
def asaas_webhook(payload: dict, request: Request, db: DbSession) -> dict:
    token = request.headers.get("asaas-access-token", "")
    if not settings.asaas_webhook_token or token != settings.asaas_webhook_token:
        raise HTTPException(status_code=401, detail="Token de webhook inválido")

    event = payload.get("event")
    payment = payload.get("payment") or {}
    if event in {"PAYMENT_CONFIRMED", "PAYMENT_RECEIVED"}:
        payment_id = payment.get("id")
        external_reference = payment.get("externalReference")
        # Defesa: reconsulta o pagamento no Asaas antes de liberar.
        try:
            real = asaas.get_payment(payment_id) if payment_id else {}
        except asaas.AsaasError:
            real = {}
        if real.get("status") in asaas.PAID_STATUSES and external_reference:
            try:
                user = db.get(User, UUID(external_reference))
            except (ValueError, TypeError):
                user = None
            if user:
                _grant_access(db, _ensure_subscription(db, user))
    return {"received": True}
