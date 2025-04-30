import pytest
import yaml
from pathlib import Path
from storage_hygiene.config_manager import ConfigManager, ConfigLoadError # Import the custom exception

# TDD Anchor: [CM_LoadDefaults] - Test loading default configuration
def test_load_default_config():
    """
    Tests that the ConfigManager loads default settings upon initialization
    when no user config is provided.
    """
    # Arrange
    # (No specific user config path provided)
    manager = ConfigManager()

    # Act
    # (Initialization loads defaults)
    default_scan_path = manager.get('scan_paths')
    default_log_level = manager.get('logging.level')
    default_min_size = manager.get('analysis.min_file_size_mb')

    # Assert
    assert isinstance(default_scan_path, list) # Expecting a list, even if empty or default
    assert default_log_level == 'INFO' # Assuming 'INFO' is the default
    assert default_min_size == 100 # Example default

# TDD Anchor: [CM_LoadUser] - Test loading user config overrides defaults
def test_load_user_config_overrides_defaults(tmp_path: Path):
    """
    Tests that loading a user config file correctly overrides default settings.
    """
    # Arrange
    user_config_content = {
        'scan_paths': ['/path/to/user/scan'],
        'logging': {
            'level': 'DEBUG' # Override default 'INFO'
        },
        'analysis': {
            'min_file_size_mb': 50 # Override default 100
        },
        'new_user_key': 'user_value'
    }
    user_config_file = tmp_path / "user_config.yaml"
    with open(user_config_file, 'w') as f:
        yaml.dump(user_config_content, f)

    # Act
    manager = ConfigManager(user_config_path=str(user_config_file))
    user_scan_path = manager.get('scan_paths')
    user_log_level = manager.get('logging.level')
    user_min_size = manager.get('analysis.min_file_size_mb')
    new_key_value = manager.get('new_user_key')

    # Assert
    assert user_scan_path == ['/path/to/user/scan']
    assert user_log_level == 'DEBUG'
    assert user_min_size == 50
    assert new_key_value == 'user_value'

# TDD Anchor: [CM_HandleMissingUserFile] - Test handling non-existent user config file
def test_handle_non_existent_user_config(tmp_path: Path):
    """
    Tests that ConfigManager uses defaults when the user config file doesn't exist.
    """
    # Arrange
    non_existent_file = tmp_path / "non_existent_config.yaml"
    # Ensure the file does not exist (tmp_path handles cleanup)
    assert not non_existent_file.exists()

    # Act
    manager = ConfigManager(user_config_path=str(non_existent_file))
    default_scan_path = manager.get('scan_paths')
    default_log_level = manager.get('logging.level')
    default_min_size = manager.get('analysis.min_file_size_mb')

    # Assert
    # Check that default values are loaded
    assert isinstance(default_scan_path, list)
    assert default_scan_path == [] # Default is empty list
    assert default_log_level == 'INFO'
    assert default_min_size == 100

# TDD Anchor: [CM_HandleInvalidUserFile] - Test handling invalid user config YAML
def test_handle_invalid_user_config_yaml(tmp_path: Path):
    """
    Tests that ConfigManager raises ConfigLoadError for invalid YAML format.
    """
    # Arrange
    invalid_yaml_content = "logging: level: DEBUG\nanalysis:\n  min_file_size_mb: 50: oops_invalid_syntax"
    invalid_config_file = tmp_path / "invalid_config.yaml"
    invalid_config_file.write_text(invalid_yaml_content)

    # Act & Assert
    with pytest.raises(ConfigLoadError) as excinfo:
        ConfigManager(user_config_path=str(invalid_config_file))

    # Optionally check the exception message contains relevant info
    assert "Error loading user config" in str(excinfo.value)
    assert "invalid_config.yaml" in str(excinfo.value)


# TDD Anchor: [CM_ValidateSchema] - Test config validation against schema
def test_validate_config_schema_invalid_type(tmp_path: Path):
    """
    Tests that ConfigManager raises ConfigLoadError for invalid schema (wrong type).
    """
    # Arrange
    # 'min_file_size_mb' should be an int/float, but provide a string
    invalid_schema_content = {
        'logging': {
            'level': 'DEBUG'
        },
        'analysis': {
            'min_file_size_mb': "should_be_number"
        }
    }
    invalid_schema_file = tmp_path / "invalid_schema.yaml"
    with open(invalid_schema_file, 'w') as f:
        yaml.dump(invalid_schema_content, f)

    # Act & Assert
    with pytest.raises(ConfigLoadError) as excinfo:
        ConfigManager(user_config_path=str(invalid_schema_file))

    assert "Invalid configuration schema" in str(excinfo.value)
    assert "'analysis.min_file_size_mb'" in str(excinfo.value) # Mention the problematic key
    assert "should be numeric" in str(excinfo.value) # Indicate the expected type


# TDD Anchor: [CM_HandleCredentials] - Test handling credential placeholders
def test_get_credential_placeholder(tmp_path: Path):
    """
    Tests that get() returns the raw placeholder string for credential keys.
    """
    # Arrange
    config_with_creds = {
        'cloud_storage': {
            'gdrive': {
                'enabled': True,
                'api_key': 'KEYRING:gdrive_api_key' # Placeholder
            },
            's3': {
                'access_key': 'ENV:AWS_ACCESS_KEY_ID' # Placeholder
            }
        },
        'logging': {'level': 'INFO'}
    }
    user_config_file = tmp_path / "creds_config.yaml"
    with open(user_config_file, 'w') as f:
        yaml.dump(config_with_creds, f)

    # Act
    manager = ConfigManager(user_config_path=str(user_config_file))
    gdrive_key = manager.get('cloud_storage.gdrive.api_key')
    s3_key = manager.get('cloud_storage.s3.access_key')
    log_level = manager.get('logging.level') # Non-credential key

    # Assert
    assert gdrive_key == 'KEYRING:gdrive_api_key' # Should return the placeholder string
    assert s3_key == 'ENV:AWS_ACCESS_KEY_ID'   # Should return the placeholder string
    assert log_level == 'INFO' # Ensure normal keys still work