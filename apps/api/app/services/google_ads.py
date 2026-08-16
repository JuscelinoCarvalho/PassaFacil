"""Conversão server-side do Google Ads via Google Ads API (uploadClickConversions).

Usa só a stdlib (urllib), no mesmo estilo de services/asaas.py — sem adicionar a
SDK oficial. O fluxo: troca o refresh token OAuth por um access token de curta
duração (cacheado em memória) e faz POST em
    customers/{customer_id}:uploadClickConversions
com o gclid, a ação de conversão, o valor e um orderId (para deduplicar com o
disparo client-side do gtag, que usa o mesmo id de transação).

Pré-requisitos (no /etc/passafacil.env, com GOOGLE_ADS_ENABLED=true):
  - developer token aprovado (Basic access) da API do Google Ads;
  - client_id/client_secret de um OAuth client "Desktop"/"Web";
  - refresh token gerado para esse client com escopo
    https://www.googleapis.com/auth/adwords;
  - customer_id (só dígitos) e o id numérico da ação de conversão "Compra";
  - login_customer_id se a conta estiver sob uma conta gerente (MCC).
"""
import json
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

from app.core.config import settings

_OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"
_ADWORDS_SCOPE = "https://www.googleapis.com/auth/adwords"

# Cache do access token OAuth (compartilhado entre requisições do processo).
_token_lock = threading.Lock()
_token_value: str | None = None
_token_expiry: float = 0.0


class GoogleAdsError(Exception):
    def __init__(self, status: int, body: str):
        self.status = status
        self.body = body
        super().__init__(f"GoogleAds {status}: {body[:500]}")


def _http(url: str, *, data: bytes | None, headers: dict, method: str) -> dict:
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            raw = response.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as error:
        raise GoogleAdsError(error.code, error.read().decode()) from None
    except urllib.error.URLError as error:
        raise GoogleAdsError(0, str(error.reason)) from None


def _access_token() -> str:
    global _token_value, _token_expiry
    with _token_lock:
        if _token_value and time.time() < _token_expiry - 60:
            return _token_value
        payload = urllib.parse.urlencode(
            {
                "client_id": settings.google_ads_client_id,
                "client_secret": settings.google_ads_client_secret,
                "refresh_token": settings.google_ads_refresh_token,
                "grant_type": "refresh_token",
            }
        ).encode()
        data = _http(
            _OAUTH_TOKEN_URL,
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        _token_value = data["access_token"]
        _token_expiry = time.time() + int(data.get("expires_in", 3600))
        return _token_value


def upload_click_conversion(
    *,
    gclid: str,
    conversion_datetime: str,
    value: float,
    currency: str,
    order_id: str,
) -> None:
    """Envia uma conversão de clique. `conversion_datetime` deve estar no formato
    exigido pela API: 'yyyy-mm-dd hh:mm:ss+00:00'. Levanta GoogleAdsError em
    qualquer falha (HTTP ou partialFailureError na resposta)."""
    customer_id = settings.google_ads_customer_id
    version = settings.google_ads_api_version
    url = (
        f"https://googleads.googleapis.com/{version}"
        f"/customers/{customer_id}:uploadClickConversions"
    )
    headers = {
        "Authorization": f"Bearer {_access_token()}",
        "developer-token": settings.google_ads_developer_token,
        "Content-Type": "application/json",
    }
    if settings.google_ads_login_customer_id:
        headers["login-customer-id"] = settings.google_ads_login_customer_id

    body = {
        "conversions": [
            {
                "gclid": gclid,
                "conversionAction": (
                    f"customers/{customer_id}/conversionActions/"
                    f"{settings.google_ads_conversion_action_id}"
                ),
                "conversionDateTime": conversion_datetime,
                "conversionValue": value,
                "currencyCode": currency,
                "orderId": order_id,
            }
        ],
        "partialFailure": True,
    }
    result = _http(url, data=json.dumps(body).encode(), headers=headers, method="POST")
    partial = result.get("partialFailureError")
    if partial:
        raise GoogleAdsError(200, json.dumps(partial))
