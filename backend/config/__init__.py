"""Configuration management for the requirements management system."""

from .config import Settings, setup_environment

# Initialize settings
settings = Settings()

# Apply environment variables
setup_environment(settings)
