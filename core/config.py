import secrets
import warnings
from typing import Annotated, Any, Literal, Optional, Union
from pydantic import (
    AnyUrl,
    BeforeValidator,
    HttpUrl,
    PostgresDsn,
    computed_field,
    model_validator,
)
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self
from dotenv import load_dotenv
import os

def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # env_file=".env", 
        env_ignore_empty=True, 
        extra="ignore"
    )
    API_V1_STR: str = "/api/v1"
    # TODO change to useing versioning with modules and this will be the naming convention
    API_VERSION_STR: str = "/api/v{version}" 
    ADMIN_PANEL_STR: str | None = "/admin"
    API_DOCS: bool = True
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ADMIN_STORAGE_KEY: str = secrets.token_urlsafe(32)
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int | None = 60 * 24 * 8
    DOMAIN: str = "localhost"
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"
    LOGGING_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    DEBUG: bool = False
    PROXY: Optional[str] = None

    @model_validator(mode="after")
    def _set_proxy_env(self) -> Self:
        if self.PROXY and self.PROXY.startswith("http"):
            os.environ["HTTP_PROXY"] = self.PROXY
            os.environ["HTTPS_PROXY"] = self.PROXY
        else:
            os.environ.pop("HTTP_PROXY", None)
            os.environ.pop("HTTPS_PROXY", None)
        return self

    APP_VERSION: str | None = "0.0.1"
    
    # @model_validator(mode="after")
    # def _force_set_app_version(self) -> Self:
    #     self.APP_VERSION = APP_VERSION
    #     return self

    @computed_field  # type: ignore[misc]
    @property
    def server_host(self) -> str:
        # Use HTTPS for anything other than local development
        if self.ENVIRONMENT == "local":
            return f"http://{self.DOMAIN}"
        return f"https://{self.DOMAIN}"

    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyUrl] | str, BeforeValidator(parse_cors)
    ] = []

    PROJECT_NAME: str
    PROJECT_DESCRIPTION: str = ""
    PROJECT_SUMMARY: str = ""
    SENTRY_DSN: Optional[Union[HttpUrl, str]] = None
    SENTRY_TRACES_SAMPLE_RATE: Optional[float] = 1.0
    SENTRY_PROFILES_SAMPLE_RATE: Optional[float] = 1.0
    
    # Database settings
    MONGODB_URI: str | None = "tinydb" # Fallback to TinyDb
    DATABASE_NAME: str | None = None
    

    REDIS_HOST: str | None = None
    REDIS_PORT: str | None = None
    REDIS_PASSWORD: str| None = None
    RQ_BYPASS_WORKER: str| None = None
    
    FASTAPI_WORKERS: int = 1
    
    @model_validator(mode="after")
    def _set_default_database_name(self) -> Self:
        if not self.MONGODB_URI or self.MONGODB_URI == "tinydb":
            self.MONGODB_URI = "tinydb" # Fallback to TinyDb
            if self.FASTAPI_WORKERS > 1:
                warnings.warn("TinyDB does not support multiple workers. Set FASTAPI_WORKERS to 1", stacklevel=1)
        if not self.DATABASE_NAME:
            self.DATABASE_NAME = self.ENVIRONMENT + "_db"
        return self

    # POSTGRES_SERVER: str| None = None
    # POSTGRES_PORT: int = 5432
    # POSTGRES_USER: str| None = None
    # POSTGRES_PASSWORD: str| None = None
    # POSTGRES_DB: str = ""

    # @computed_field  # type: ignore[misc]
    # @property
    # def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
    #     if not self.POSTGRES_SERVER:
    #         return None
    #     return MultiHostUrl.build(
    #         scheme="postgresql+psycopg",
    #         username=self.POSTGRES_USER,
    #         password=self.POSTGRES_PASSWORD,
    #         host=self.POSTGRES_SERVER,
    #         port=self.POSTGRES_PORT,
    #         path=self.POSTGRES_DB,
    #     )

    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_PORT: int = 587
    SMTP_HOST: str | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    # TODO: update type to EmailStr when sqlmodel supports it
    EMAILS_FROM_EMAIL: str | None = None
    EMAILS_FROM_NAME: str | None = None

    @model_validator(mode="after")
    def _set_default_emails_from(self) -> Self:
        if not self.EMAILS_FROM_NAME:
            self.EMAILS_FROM_NAME = self.PROJECT_NAME
        return self

    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48

    @computed_field  # type: ignore[misc]
    @property
    def emails_enabled(self) -> bool:
        return bool(self.SMTP_HOST and self.EMAILS_FROM_EMAIL)

    # TODO: update type to EmailStr when sqlmodel supports it
    EMAIL_TEST_USER: str = "test@example.com"
    # TODO: update type to EmailStr when sqlmodel supports it
    FIRST_SUPERUSER: str
    FIRST_SUPERUSER_PASSWORD: str
    USERS_OPEN_REGISTRATION: bool = False

    def _check_default_secret(self, var_name: str, value: str | None) -> None:
        if value == "changethis":
            message = (
                f'The value of {var_name} is "changethis", '
                "for security, please change it, at least for deployments."
            )
            if self.ENVIRONMENT == "local":
                warnings.warn(message, stacklevel=1)
            else:
                raise ValueError(message)

    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        self._check_default_secret("SECRET_KEY", self.SECRET_KEY)
        # self._check_default_secret("POSTGRES_PASSWORD", self.POSTGRES_PASSWORD)
        self._check_default_secret(
            "FIRST_SUPERUSER_PASSWORD", self.FIRST_SUPERUSER_PASSWORD
        )

        return self


# settings = Settings()  # type: ignore
# Load the .env file manually
# TODO Have different env files/docker secrets for different environments
load_dotenv(override=True, verbose=True, dotenv_path=".env", encoding="utf-8")

# Create an instance of Settings
# This will use the values from the .env file, overriding any environment variables
settings = Settings(_env_file=os.path.abspath(".env"), _env_file_encoding='utf-8') # type: ignore