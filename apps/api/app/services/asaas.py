import json
import urllib.error
import urllib.request

from app.core.config import settings


class AsaasError(Exception):
    def __init__(self, status: int, body: str):
        self.status = status
        self.body = body
        super().__init__(f"Asaas {status}: {body}")


def _request(method: str, path: str, payload: dict | None = None) -> dict:
    url = settings.asaas_base + path
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "access_token": settings.asaas_key,
            "Content-Type": "application/json",
            "User-Agent": "PassaFacil/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            raw = response.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as error:
        raise AsaasError(error.code, error.read().decode()) from None


def create_customer(name: str, email: str, cpf_cnpj: str) -> dict:
    return _request("POST", "/customers", {"name": name, "email": email, "cpfCnpj": cpf_cnpj})


def create_pix_payment(customer_id: str, value: float, description: str, external_reference: str, due_date: str) -> dict:
    return _request(
        "POST",
        "/payments",
        {
            "customer": customer_id,
            "billingType": "PIX",
            "value": value,
            "dueDate": due_date,
            "description": description,
            "externalReference": external_reference,
        },
    )


def get_pix_qr(payment_id: str) -> dict:
    return _request("GET", f"/payments/{payment_id}/pixQrCode")


def get_payment(payment_id: str) -> dict:
    return _request("GET", f"/payments/{payment_id}")


def delete_payment(payment_id: str) -> dict:
    return _request("DELETE", f"/payments/{payment_id}")


PAID_STATUSES = {"CONFIRMED", "RECEIVED", "RECEIVED_IN_CASH"}
