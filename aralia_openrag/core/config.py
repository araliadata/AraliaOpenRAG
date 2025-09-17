"""Configuration management for Aralia OpenRAG."""

from pydantic_settings import BaseSettings
from typing import Optional, Literal


class AraliaConfig(BaseSettings):
    """Unified configuration management for Aralia OpenRAG.
    
    This class manages all configuration settings including API credentials,
    LLM settings, and execution parameters. Settings can be provided via
    environment variables or .env file.
    """
    
    # Aralia API Configuration
    aralia_sso_url: str = "https://sso.araliadata.io"
    aralia_stellar_url: str = "https://tw-air.araliadata.io"
    aralia_client_id: Optional[str] = None
    aralia_client_secret: Optional[str] = None
    
    # LLM Configuration
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    
    # Default LLM models
    openai_model: str = "gpt-4o"
    anthropic_model: str = "claude-3-5-sonnet-20240620"
    google_model: str = "gemini-2.0-flash"
    
    # Execution Configuration
    max_retries: int = 3
    timeout_seconds: int = 30
    temperature: float = 0.0
    verbose: bool = False
    
    # Advanced options
    enable_checkpointing: bool = True
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
    def get_llm_config(self, api_key: str) -> dict:
        """Determine LLM configuration based on API key prefix.
        
        Args:
            api_key: The API key to analyze
            
        Returns:
            Dictionary containing LLM type and configuration
        """
        if api_key.startswith('sk-ant-'):
            return {
                "provider": "anthropic",
                "model": self.anthropic_model,
                "api_key": api_key
            }
        elif api_key.startswith('AIza'):
            return {
                "provider": "google",
                "model": self.google_model,
                "api_key": api_key
            }
        else:
            return {
                "provider": "openai", 
                "model": self.openai_model,
                "api_key": api_key
            }
            
    def validate_required_settings(self) -> None:
        """Validate that all required settings are present.
        
        Raises:
            ValueError: If required settings are missing
        """
        required_fields = [
            ("aralia_client_id", self.aralia_client_id),
            ("aralia_client_secret", self.aralia_client_secret)
        ]
        
        missing_fields = [
            field_name for field_name, field_value in required_fields
            if field_value is None
        ]
        
        if missing_fields:
            raise ValueError(
                f"Missing required configuration fields: {', '.join(missing_fields)}"
            )
