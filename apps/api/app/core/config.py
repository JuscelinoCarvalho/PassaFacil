from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Passa Fácil API"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./passafacil.db"
    jwt_secret: str = "local-development-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    cors_origins: str = "http://localhost:9001"
    owner_mode: bool = True
    owner_email: str = "juscelino@passafacil.local"
    question_import_dir: str = "./data/imports"
    max_pdf_upload_mb: int = 50

    site_url: str = "https://passafacil.jussa.com.br"
    email_verify_token_hours: int = 48
    # Para onde vão as mensagens de ajuda/reclamação do widget "Fale conosco".
    # Listas separadas por vírgula. support_bcc = cópia oculta.
    support_to: str = "jussa@jussa.com.br,mitsuplick@protonmail.com"
    support_bcc: str = "juscelino.carvalho@gmail.com"

    # Pagamento (Asaas)
    asaas_sandbox: bool = True
    asaas_api_base: str = "https://api.asaas.com/v3"
    asaas_api_base_sandbox: str = "https://api-sandbox.asaas.com/v3"
    asaas_api_key: str = ""
    asaas_api_key_sandbox: str = ""
    asaas_webhook_token: str = ""
    price_reais: float = 100.0

    # Conversão server-side do Google Ads (Google Ads API — uploadClickConversions).
    # Quando ligado e com o gclid do comprador em mãos, a conversão "Compra" é
    # enviada direto pela API ao confirmar o Pix — sem depender do gtag no navegador.
    # Desligado por padrão: exige developer token aprovado + refresh token OAuth.
    google_ads_enabled: bool = False
    google_ads_api_version: str = "v18"
    google_ads_developer_token: str = ""
    google_ads_client_id: str = ""
    google_ads_client_secret: str = ""
    google_ads_refresh_token: str = ""
    google_ads_customer_id: str = ""  # só dígitos, sem hífens (ex.: 6402992934)
    google_ads_login_customer_id: str = ""  # conta gerente (MCC), se houver
    google_ads_conversion_action_id: str = ""  # id numérico da ação "Compra"

    # --- Correção por IA das discursivas (cascata de provedores GRATUITOS) ---
    # A correção compara a resposta do aluno com o espelho + a grade de critérios
    # e atribui a nota final de cada critério. Usa uma cascata: tenta cada
    # provedor na ordem de `grading_order` e cai para o próximo em caso de falha
    # ou limite de uso. Todos expõem endpoint compatível com a API OpenAI
    # (/chat/completions), então o código é o mesmo para todos — só muda a
    # base_url, o modelo e a chave. Preencha só as chaves que tiver; provedor sem
    # chave é pulado. Sem nenhuma chave (ou se todos falharem), o app cai na
    # autoavaliação manual — nada quebra.
    grading_enabled: bool = True
    # Ordem padrão só com provedores 100% gratuitos e sem cartão (Groq/Gemini/
    # Cerebras). A OpenRouter fica FORA por padrão: os modelos :free custam US$0,
    # mas a plataforma exige crédito/cartão para limites úteis. Ela continua
    # suportada — basta incluir "openrouter" no GRADING_ORDER e a chave no /etc.
    grading_order: str = "groq,gemini"
    grading_timeout_seconds: int = 40

    # Groq — camada grátis generosa e muito rápida (https://console.groq.com)
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    groq_base_url: str = "https://api.groq.com/openai/v1"

    # Google Gemini — endpoint compatível com OpenAI (https://aistudio.google.com)
    # Usa o alias "-latest": contas novas não têm acesso a versões antigas pinadas
    # (ex.: gemini-2.0/2.5-flash dão 404 "no longer available to new users"), então
    # o alias auto-acompanha o flash atual e evita quebrar em deprecações.
    gemini_api_key: str = ""
    gemini_model: str = "gemini-flash-latest"
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai"

    # OpenRouter — OPCIONAL/fora da cascata padrão: modelos :free custam US$0, mas
    # a plataforma pede crédito/cartão para limites úteis (https://openrouter.ai)
    openrouter_api_key: str = ""
    openrouter_model: str = "deepseek/deepseek-chat-v3-0324:free"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # Cerebras — PARADO/fora da cascata: exige crédito/cartão (retorna
    # payment_required no tier grátis). Chave já validada; retomar quando crescer
    # a base de assinantes incluindo "cerebras" no GRADING_ORDER. (cloud.cerebras.ai)
    cerebras_api_key: str = ""
    cerebras_model: str = "gpt-oss-120b"  # modelo válido nesta conta (não há Llama)
    cerebras_base_url: str = "https://api.cerebras.ai/v1"

    @property
    def grading_provider_order(self) -> list[str]:
        return [p.strip().lower() for p in self.grading_order.split(",") if p.strip()]

    @property
    def google_ads_ready(self) -> bool:
        return self.google_ads_enabled and all(
            [
                self.google_ads_developer_token,
                self.google_ads_client_id,
                self.google_ads_client_secret,
                self.google_ads_refresh_token,
                self.google_ads_customer_id,
                self.google_ads_conversion_action_id,
            ]
        )

    @property
    def asaas_base(self) -> str:
        return self.asaas_api_base_sandbox if self.asaas_sandbox else self.asaas_api_base

    @property
    def asaas_key(self) -> str:
        return self.asaas_api_key_sandbox if self.asaas_sandbox else self.asaas_api_key
    smtp_host: str = "127.0.0.1"
    smtp_port: int = 25
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_tls: bool = False
    smtp_from: str = "Passa Fácil <noreply@jussa.com.br>"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def support_to_list(self) -> list[str]:
        return [item.strip() for item in self.support_to.split(",") if item.strip()]

    @property
    def support_bcc_list(self) -> list[str]:
        return [item.strip() for item in self.support_bcc.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
