from pydantic_settings import BaseSettings  # Corrected import


class Settings(BaseSettings):
    app_name:str
    
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int

    postgresql_database: str

    smtp_server: str
    smtp_port: int
    email_address: str
    email_password: str

    class Config:
        env_file = ".env"


settings = Settings()
