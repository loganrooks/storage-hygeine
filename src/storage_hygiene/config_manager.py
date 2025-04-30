import yaml
import os
from typing import Any, Optional, Dict, List

# Custom Exception for configuration loading errors
class ConfigLoadError(Exception):
    """Custom exception for errors during configuration loading."""
    pass

class ConfigManager:
    """Manages loading and accessing configuration settings."""

    def __init__(self, user_config_path: Optional[str] = None):
        """
        Initializes the ConfigManager, loading default and user configurations.

        Args:
            user_config_path: Optional path to the user's configuration file.
        """
        self._config: Dict[str, Any] = self._load_defaults()
        user_config = self._load_user_config(user_config_path) # Might raise ConfigLoadError
        if user_config:
            self._config = self._merge_configs(self._config, user_config)

        # Validate the final merged configuration
        self._validate_schema() # Might raise ConfigLoadError

    def _load_defaults(self) -> Dict[str, Any]:
        """Loads the default configuration settings."""
        # Minimal defaults to pass the first test
        return {
            "scan_paths": [],
            "logging": {
                "level": "INFO"
            },
            "analysis": {
                "min_file_size_mb": 100
            }
            # More defaults will be added based on pseudocode/requirements
        }

    def _load_user_config(self, path: Optional[str]) -> Optional[Dict[str, Any]]:
        """Loads configuration from a YAML file."""
        if path and os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    user_data = yaml.safe_load(f)
                    # Ensure loaded data is a dictionary. If not, raise ConfigLoadError.
                    if not isinstance(user_data, dict):
                        raise ConfigLoadError(f"Error loading user config '{path}': Root element is not a dictionary.")
                    return user_data
            except yaml.YAMLError as e:
                # Raise ConfigLoadError, wrapping the original YAMLError
                raise ConfigLoadError(f"Error loading user config '{path}': Invalid YAML format - {e}") from e
            except IOError as e:
                # Handle file reading errors later (maybe raise ConfigLoadError too?)
                print(f"Warning: Could not read user config '{path}': {e}")
                return None
        return None

    def _merge_configs(self, base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merges the updates dict into the base dict."""
        merged = base.copy()  # Start with a copy of the base dictionary
        for key, value in updates.items():
            if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        return merged

    def _validate_schema(self):
        """Performs basic validation of the loaded configuration."""
        # Minimal validation to pass the current test
        min_size = self.get('analysis.min_file_size_mb')
        if not isinstance(min_size, (int, float)):
             raise ConfigLoadError(
                 f"Invalid configuration schema: 'analysis.min_file_size_mb' "
                 f"should be numeric, but got type {type(min_size).__name__}."
             )
        # Add more validation checks as needed for other keys/types later

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """
        Retrieves a configuration value using dot notation.

        Args:
            key: The configuration key (e.g., 'logging.level').
            default: The default value to return if the key is not found.

        Returns:
            The configuration value or the default.
        """
        keys = key.split('.')
        value = self._config
        try:
            for k in keys:
                if isinstance(value, dict):
                    value = value[k]
                else:
                    # Handle cases where intermediate key is not a dict
                    return default
            return value
        except (KeyError, TypeError):
            return default

# Example usage (optional, for basic verification)
if __name__ == '__main__':
    manager = ConfigManager()
    print(f"Default Log Level: {manager.get('logging.level')}")
    print(f"Default Scan Paths: {manager.get('scan_paths')}")
    print(f"Non-existent key: {manager.get('non.existent.key', 'Not Found')}")
    print(f"Min File Size: {manager.get('analysis.min_file_size_mb')}")