from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    tei_url: str = "http://localhost:8002"
    tei_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chroma_host: str = "localhost"
    chroma_port: int = 8000
    mcp_port: int = 8001
    kb_path: str = "data/knowledge_base.jsonl"

    @property
    def tei_base_url(self) -> str:
        return self.tei_url.rstrip("/")