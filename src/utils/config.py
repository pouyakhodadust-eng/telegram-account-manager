"""
Telegram Account Manager - Configuration Loader

Loads configuration from config.yaml and supports environment variable overrides.
"""

import os
from pathlib import Path
from typing import Any, Optional

import yaml


class Config:
    """
    Configuration manager that loads from YAML and supports env overrides.
    
    Usage:
        config = Config()
        value = config.get("database.host")
        db_port = config.get("database.port", 5432)
    """
    
    _instance: Optional["Config"] = None
    _config: dict = {}
    
    def __new__(cls) -> "Config":
        """Singleton pattern to ensure single config instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self) -> None:
        """Load configuration from config.yaml."""
        config_path = Path(__file__).parent.parent.parent / "config.yaml"
        
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f) or {}
        else:
            self._config = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.
        
        Args:
            key: Configuration key using dot notation (e.g., "database.host")
            default: Default value if key not found
            
        Returns:
            Configuration value or default
            
        Examples:
            config.get("database.host")  # Returns "localhost"
            config.get("database.port", 5432)  # Returns 5432 or default
        """
        # Check for environment variable override first
        env_key = key.upper().replace(".", "_")
        env_value = os.environ.get(env_key)
        if env_value is not None:
            # Try to parse as the right type
            return self._parse_env_value(env_value, default)
        
        # Navigate the config dictionary
        keys = key.split(".")
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def _parse_env_value(self, env_value: str, default: Any) -> Any:
        """Parse environment variable string to appropriate type."""
        if default is None:
            return env_value
        
        default_type = type(default)
        
        if default_type == bool:
            return env_value.lower() in ("true", "1", "yes")
        elif default_type == int:
            try:
                return int(env_value)
            except ValueError:
                return default
        elif default_type == float:
            try:
                return float(env_value)
            except ValueError:
                return default
        else:
            return env_value
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value using dot notation.
        
        Args:
            key: Configuration key using dot notation
            value: Value to set
        """
        keys = key.split(".")
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def reload(self) -> None:
        """Reload configuration from file."""
        self._load_config()
    
    @property
    def all(self) -> dict:
        """Get the entire configuration dictionary."""
        return self._config.copy()


# Global config instance
config = Config()


def load_config(config_path: Optional[str] = None) -> dict:
    """
    Load configuration from a specific file path.
    
    Args:
        config_path: Path to config.yaml file. If None, uses default location.
        
    Returns:
        Configuration dictionary
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent.parent / "config.yaml"
    
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}
