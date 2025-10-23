"""Configuration management for the requirements management system."""
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Keys
    groq_api_key: str = ""
    langchain_api_key: str = ""
    
    # LangChain Settings
    langchain_tracing_v2: str = "true"
    langchain_endpoint: str = "https://api.smith.langchain.com"
    langchain_project: str = "reqmgmt"
    
    # Neo4j Settings
    neo4j_url: str = "bolt://localhost:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str = ""
    neo4j_database: str = "requirements-management"
    
    # LLM Settings
    llm_model: str = "llama-3.1-8b-instant"
    
    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_title: str = "Requirements Management API"
    api_version: str = "1.0.0"
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "requirements_management.log"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

def setup_environment(settings: Settings):
    """Set up environment variables from settings."""
    # os.environ["GROQ_API_KEY"] = settings.groq_api_key
    # os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
    # os.environ["LANGCHAIN_TRACING_V2"] = settings.langchain_tracing_v2
    # os.environ["LANGCHAIN_ENDPOINT"] = settings.langchain_endpoint
    # os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project
    import os
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
    os.environ["LANGCHAIN_API_KEY"] = ""
    os.environ["LANGCHAIN_PROJECT"] = "reqmgmt"
    os.environ["GROQ_API_KEY"] = ""

settings = Settings()
setup_environment(settings)

