from pathlib import Path
from typing import List, Optional

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent
ROOT_DIR = BACKEND_DIR.parent
BACKEND_ENV_FILE = BACKEND_DIR / ".env"

_DEFAULT_ORIGINS = (
    "http://localhost:3000,"
    "http://localhost:3001,"
    "https://mazaya-website.vercel.app,"
    "https://mazaya-admin.vercel.app"
)


class Settings(BaseSettings):
    groq_api_key: str = ""
    groq_model: str = Field(
        default="llama-3.3-70b-versatile",
        validation_alias=AliasChoices("GROQ_MODEL", "MODEL", "model"),
    )
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    database_url: str = "sqlite:///./data/mazaya_fm.db"
    secret_key: str = "dev-secret-key-change-in-prod"
    # ALLOWED_ORIGINS overrides the default list; CORS_ORIGINS is a legacy alias.
    # Use ALLOWED_ORIGINS=* to allow requests from any frontend origin.
    allowed_origins: str = _DEFAULT_ORIGINS
    cors_origins: str = ""          # kept for backwards compat — merged below
    admin_username: str = "admin"
    admin_password: str = "Admin@Mazaya2025"
    auto_approval_threshold_kd: float = 500.0
    lead_score_hot_threshold: float = 70.0
    lead_score_warm_threshold: float = 40.0
    vendor_dispatch_timeout_minutes: int = 30
    p1_sla_hours: int = 2
    p2_sla_hours: int = 8
    p3_sla_hours: int = 48
    briefing_daily_cron: str = "0 8 * * *"
    briefing_weekly_cron: str = "0 9 * * 1"

    @model_validator(mode="after")
    def normalize_database_url(self):
        prefix = "sqlite:///"
        if not self.database_url.startswith(prefix) or self.database_url.startswith("sqlite:////"):
            return self

        raw_path = self.database_url[len(prefix):]
        if raw_path == ":memory:":
            return self

        db_path = Path(raw_path)
        if db_path.is_absolute():
            return self

        if db_path.parts and db_path.parts[0] == "backend":
            resolved = ROOT_DIR / db_path
        elif db_path.parts and db_path.parts[0] == "data":
            resolved = BACKEND_DIR / db_path
        else:
            resolved = BACKEND_DIR / db_path

        self.database_url = f"sqlite:///{resolved.resolve().as_posix()}"
        return self

    @property
    def _cors_origin_values(self) -> List[str]:
        combined = []
        for raw in (self.allowed_origins, self.cors_origins):
            for o in raw.split(","):
                o = o.strip()
                if o and o not in combined:
                    combined.append(o)
        return combined

    @property
    def allow_all_origins(self) -> bool:
        return "*" in self._cors_origin_values

    @property
    def cors_origins_list(self) -> List[str]:
        if self.allow_all_origins:
            return []
        return self._cors_origin_values

    @property
    def cors_origin_regex(self) -> Optional[str]:
        if self.allow_all_origins:
            return ".*"
        return None

    model_config = SettingsConfigDict(
        env_file=str(BACKEND_ENV_FILE),
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
