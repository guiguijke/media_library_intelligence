import logging
import warnings
from typing import Optional

from passlib.context import CryptContext
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

# bcrypt hash for the default password "admin". Generated with bcrypt 4.1.3 / passlib 1.7.4.
# This is intentionally verbose: if ADMIN_PASSWORD_HASH is not overridden, a warning is logged.
DEFAULT_ADMIN_PASSWORD_HASH = "$2b$12$yzvdd6qsIPemzshXkqPWJeyqCUhgYZQBlDXyX3VwwxM1R0EPm233W"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Media Library Intelligence"
    DEBUG: bool = False

    # Security
    SECRET_KEY: Optional[str] = None
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD_HASH: str = DEFAULT_ADMIN_PASSWORD_HASH

    # CORS
    ALLOWED_ORIGINS: str = ""  # comma-separated list, used when DEBUG=False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/mli"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Celery
    CELERY_BROKER_URL: str = ""
    CELERY_RESULT_BACKEND: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.CELERY_BROKER_URL:
            self.CELERY_BROKER_URL = self.REDIS_URL
        if not self.CELERY_RESULT_BACKEND:
            self.CELERY_RESULT_BACKEND = self.REDIS_URL
        self._validate_secret_key()
        self._validate_admin_password()

    def _validate_secret_key(self) -> None:
        if not self.SECRET_KEY:
            if self.DEBUG:
                warnings.warn(
                    "SECRET_KEY is not set. Using a deterministic development key. "
                    "Set a strong SECRET_KEY environment variable before deploying to production.",
                    stacklevel=2,
                )
                self.SECRET_KEY = "dev-secret-key-not-safe-for-production-use-only"
            else:
                raise ValueError(
                    "SECRET_KEY environment variable is required in production (DEBUG=False)."
                )
        elif len(self.SECRET_KEY) < 32:
            if self.DEBUG:
                warnings.warn(
                    f"SECRET_KEY is only {len(self.SECRET_KEY)} characters long. "
                    "Use at least 32 cryptographically random characters in production.",
                    stacklevel=2,
                )
            else:
                raise ValueError(
                    "SECRET_KEY must be at least 32 characters long in production (DEBUG=False)."
                )

    def _validate_admin_password(self) -> None:
        if self.ADMIN_PASSWORD_HASH == DEFAULT_ADMIN_PASSWORD_HASH:
            logger.warning(
                "ADMIN_PASSWORD_HASH is using the default insecure value for user '%s'. "
                "Override ADMIN_PASSWORD_HASH in production!",
                self.ADMIN_USERNAME,
            )

    def verify_admin_password(self, plain_password: str) -> bool:
        """Verify the provided password against the configured admin password hash."""
        try:
            return pwd_context.verify(plain_password, self.ADMIN_PASSWORD_HASH)
        except Exception:
            return False


settings = Settings()
