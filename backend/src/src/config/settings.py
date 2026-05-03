from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_HOST: str = "db"
    DB_PORT: int = 5432
    DB_NAME: str = "web_crawler"
    DB_USER: str = "myuser"
    DB_PASSWORD: str = "mypassword"

    DATABASE_URL: Optional[str] = None
    DB_REQUIRE_SSL: bool = False
    MIGRATION_DATABASE_URL: Optional[str] = None

    R2_ACCOUNT_ID: Optional[str] = None
    R2_ACCESS_KEY_ID: Optional[str] = None
    R2_SECRET_ACCESS_KEY: Optional[str] = None
    R2_BUCKET: Optional[str] = None
    R2_PUBLIC_URL: Optional[str] = None

    @property
    def database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def migration_database_url(self) -> str:
        return self.MIGRATION_DATABASE_URL or self.database_url

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
