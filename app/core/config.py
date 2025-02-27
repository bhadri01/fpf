from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name:str
    app_version:str
    app_url:str
    base_path:str

    verify_url:str
    reset_url:str

    secret_key: str
    algorithm: str
    access_token_expire_minutes: int

    postgresql_database_master_url: str
    postgresql_database_slave_url: str

    mail_username: str
    mail_password: str
    mail_from: str
    mail_port: int
    mail_server: str
    mail_starttls: bool
    mail_ssl_tls: bool
    use_credentials: bool
    validate_certs: bool
    mail_from_name: str
    template_folder: str

    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    minio_secure: bool
    minio_bucket: str

    redis_url: str
    
    environment: str

    class Config:
        env_file = ".env"

settings = Settings()