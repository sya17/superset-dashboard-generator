from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Superset API config
    SUPERSET_URL: str = "http://localhost:8088"
    # SUPERSET_URL: str = "http://demo.supersert.pkp.co.id"
    # SUPERSET_API_USER: str = "superset.ai"
    # SUPERSET_API_PASS: str = "12345"
    # Try different user - comment/uncomment as needed
    SUPERSET_API_USER: str = "admin"
    SUPERSET_API_PASS: str = "admin"

    MODEL_AI_URL: str = ""

    MODEL_AI_KEY: str = "AIzaSyCCMVkLoOZdqIl2gy98yBe_2adqSwtiJzQ"
    MODEL_AI: str = "gemini-1.5-flash"
    DEFAULT_LLM_PROVIDER: str = "gemini"

    # MODEL_AI_KEY: str = "csk-4vkwt45ex8p4pwcv9e8e9vm3hw556mj562eh8dxv8peech6t"
    # MODEL_AI: str = "qwen-3-coder-480b"
    # DEFAULT_LLM_PROVIDER: str ="cerebras"
    
    # Default LLM Provider to use
    # DEFAULT_LLM_PROVIDER: str ="local_qwen"
    # DEFAULT_LLM_PROVIDER: str ="openai"

    # Application settings
    # LOG_LEVEL: str = "DEBUG"
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8', extra='ignore')

settings = Settings()
