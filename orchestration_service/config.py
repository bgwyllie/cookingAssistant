from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    QUERY_URL: str = "http://localhost:8001"
    SEARCH_URL: str = "http://localhost:8002"
    HTML_URL: str = "http://localhost:8003"
    EXTRACT_URL: str = "http://localhost:8004"
    RANK_URL: str = "http://localhost:8005"
    SUMMARY_URL: str = "http://localhost:8006"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
