"""
Configuration loader for the SMART STOCK TRADING SYSTEM.
"""

import yaml
import os
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigLoader:
    """Load and manage system configuration."""
    
    def __init__(self, config_path: str = "config/settings.yaml"):
        self.config_path = config_path
        self._config = None
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as file:
                self._config = yaml.safe_load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML configuration: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key (supports nested keys with dot notation)."""
        if self._config is None:
            self._load_config()
        
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_data_engine_config(self) -> Dict[str, Any]:
        """Get data engine configuration."""
        return self.get('data_engine', {})
    
    def get_indicators_config(self) -> Dict[str, Any]:
        """Get indicators configuration."""
        return self.get('indicators', {})
    
    def get_strategies_config(self) -> Dict[str, Any]:
        """Get strategies configuration."""
        return self.get('strategies', {})
    
    def get_backtesting_config(self) -> Dict[str, Any]:
        """Get backtesting configuration."""
        return self.get('backtesting', {})
    
    def get_risk_management_config(self) -> Dict[str, Any]:
        """Get risk management configuration."""
        return self.get('risk_management', {})
    
    def get_dashboard_config(self) -> Dict[str, Any]:
        """Get dashboard configuration."""
        return self.get('dashboard', {})
    
    def reload(self) -> None:
        """Reload configuration from file."""
        self._load_config()
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get full configuration dictionary."""
        if self._config is None:
            self._load_config()
        return self._config


# Global config instance
config = ConfigLoader() 