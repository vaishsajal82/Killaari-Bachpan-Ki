"""
config.py — centralized application settings, loaded from environment
variables (or a .env file during local development).
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str = "sqlite:///./kilkaari_dev.db"

    # Auth
    jwt_secret_key: str = "dev-only-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # First admin, auto-created on startup if no admin exists yet
    first_admin_email: str = "admin@kilkaari.org.in"
    first_admin_password: str = "change-this-immediately"
    first_admin_name: str = "Kilkaari Admin"

    # CORS — comma-separated origins. Defaults to "*" (allow any origin) so
    # that if CORS_ORIGINS is never explicitly set (e.g. forgotten in a
    # hosting dashboard's environment variables — note that hosts like
    # Render do NOT read a committed .env file's values over their own
    # dashboard settings being *absent*; if no var is set there and no .env
    # is deployed, this default is what actually applies), the site doesn't
    # silently lock out its own admin portal. Once you have fixed
    # production domains, set CORS_ORIGINS explicitly to that comma
    # separated list instead of relying on this default.
    cors_origins: str = "*"

    # Payments
    payment_provider: str = "test"
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    instamojo_api_key: str = ""
    instamojo_auth_token: str = ""

    # Cloudinary — used by app/cloudinary_service.py for persistent image
    # storage (see app/routers/uploads.py). Left blank by default rather
    # than required, since local dev / tests that never touch the upload
    # endpoint shouldn't be forced to have Cloudinary credentials just to
    # start the app — uploads.py checks these are actually set at the
    # moment an upload is attempted, not at startup.
    cloudinary_cloud_name: str = ""
    cloudinary_api_key: str = ""
    cloudinary_api_secret: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
