import os
import shutil
import pytest
from unittest.mock import Mock

from storage_hygiene.action_executor import ActionExecutor
# from storage_hygiene.config_manager import ConfigManager # Keep commented for now, using Mock

def test_action_executor_initialization():
    """
    Test that ActionExecutor can be initialized with a ConfigManager.
    TDD Anchor: [AX_Init]
    """
    mock_config_manager = Mock()
    # Test will fail here initially as ActionExecutor doesn't exist yet
    mock_metadata_store = Mock() # Add mock store
    executor = ActionExecutor(config_manager=mock_config_manager, metadata_store=mock_metadata_store)
    assert executor is not None
    assert executor.config_manager == mock_config_manager

# Add more tests later following the TDD cycle
from pathlib import Path
from unittest.mock import call # Add call import

# ... (keep existing test_action_executor_initialization)

def test_execute_actions_retrieves_config(mocker): # Use pytest-mock fixture
    """
    Test that execute_actions retrieves staging_dir and dry_run config.
    TDD Anchor: [AX_LoadConfig]
    """
    mock_config_manager = mocker.Mock()
    # Configure return values for expected calls
    mock_config_manager.get.side_effect = lambda key, default=None: {
        'action_executor.staging_dir': '/tmp/staging', # Corrected key
        'action_executor.dry_run': False # Corrected key
    }.get(key, default)

    mock_metadata_store = mocker.Mock() # Add mock store
    executor = ActionExecutor(config_manager=mock_config_manager, metadata_store=mock_metadata_store)

    # Call execute_actions with an empty list for now
    executor.execute_actions({}) # Pass empty dict, not list

    # Assert that config_manager.get was called correctly
    expected_calls = [
        call('action_executor.staging_dir', './.storage_hygiene_staging'), # Expect string default as used in ActionExecutor
        call('action_executor.dry_run', False) # Corrected key
    ]
    mock_config_manager.get.assert_has_calls(expected_calls, any_order=True)
# ... (keep existing tests)

def test_execute_actions_dispatches_stage_duplicate(mocker):
    """
    Test that execute_actions calls the internal method for 'stage_duplicate'.
    TDD Anchor: [AX_Dispatch]
    """
    mock_config_manager = mocker.Mock()
    mock_config_manager.get.side_effect = lambda key, default=None: {
        'action_executor.staging_dir': './.storage_hygiene_staging', # Corrected key and use default path
        'action_executor.dry_run': False # Corrected key
    }.get(key, default)

    # Mock the internal method we expect to be called *before* instance creation
    mock_stage_method = mocker.patch('storage_hygiene.action_executor.ActionExecutor._stage_duplicate', return_value=None)

    mock_metadata_store = mocker.Mock() # Add mock store
    executor = ActionExecutor(config_manager=mock_config_manager, metadata_store=mock_metadata_store)

    action_details = {
        'action': 'stage_duplicate',
        'path': '/path/to/duplicate.txt',
        'hash': 'aabbcc',
        'original': '/path/to/original.txt'
    }
    actions_list = [action_details]

    executor.execute_actions({'stage_duplicate': actions_list}) # Pass dict format

    # Assert that the *patched* method was called with the details
    mock_stage_method.assert_called_once_with(action_details, Path('./.storage_hygiene_staging'), False) # Use default path
# ... (keep existing tests)

def test_stage_duplicate_moves_file(mocker):
    """
    Test that _stage_duplicate calculates the correct path and calls move/makedirs.
    TDD Anchor: [AX_StageDup], [AX_FileSystem]
    """
    mock_config_manager = mocker.Mock()
    # No need to mock get here as we call _stage_duplicate directly

    # Mock file system operations
    mock_makedirs = mocker.patch('os.makedirs')
    mock_move = mocker.patch('shutil.move')
    # Mock Path.exists to simulate destination not existing initially
    mocker.patch('pathlib.Path.exists', return_value=False)


    mock_metadata_store = mocker.Mock() # Add mock store
    executor = ActionExecutor(config_manager=mock_config_manager, metadata_store=mock_metadata_store)

    staging_dir = Path('/tmp/staging')
    dry_run = False
    file_hash = 'aabbccddeeff'
    file_path = Path('/path/to/some/duplicate.txt')
    action_details = {
        'action': 'stage_duplicate',
        'path': str(file_path), # Ensure path is string as expected from analysis
        'hash': file_hash,
        'original': '/path/to/original.txt'
    }

    # Calculate expected destination
    expected_dest_dir = staging_dir / 'duplicates' / file_hash[:2] / file_hash
    expected_dest_path = expected_dest_dir / file_path.name

    # Call the method directly
    executor._stage_duplicate(action_details, staging_dir, dry_run)

    # Assertions
    mock_makedirs.assert_called_once_with(expected_dest_dir, exist_ok=True)
    mock_move.assert_called_once_with(str(file_path), expected_dest_path)
# ... (keep existing tests)

def test_stage_duplicate_dry_run_logs_and_skips_move(mocker):
    """
    Test that _stage_duplicate skips move/makedirs and logs when dry_run is True.
    TDD Anchor: [AX_DryRun], [AX_StageDup]
    """
    mock_config_manager = mocker.Mock()
    # No need to mock get here as we call _stage_duplicate directly

    # Mock file system operations and print
    mock_makedirs = mocker.patch('os.makedirs')
    mock_move = mocker.patch('shutil.move')
    mock_print = mocker.patch('builtins.print') # Mock print for logging check

    mock_metadata_store = mocker.Mock() # Add mock store
    executor = ActionExecutor(config_manager=mock_config_manager, metadata_store=mock_metadata_store)

    staging_dir = Path('/tmp/staging')
    dry_run = True # <--- Set dry_run to True
    file_hash = 'aabbccddeeff'
    file_path = Path('/path/to/some/duplicate.txt')
    action_details = {
        'action': 'stage_duplicate',
        'path': str(file_path),
        'hash': file_hash,
        'original': '/path/to/original.txt'
    }

    # Calculate expected destination (needed for log message)
    expected_dest_dir = staging_dir / 'duplicates' / file_hash[:2] / file_hash
    expected_dest_path = expected_dest_dir / file_path.name

    # Call the method directly
    executor._stage_duplicate(action_details, staging_dir, dry_run)

    # Assertions
    mock_makedirs.assert_not_called()
    mock_move.assert_not_called()
    mock_print.assert_any_call(f"[DRY RUN] Would move {file_path} to {expected_dest_path}")
# ... (keep existing tests)

def test_execute_actions_dispatches_review_large(mocker):
    """
    Test that execute_actions calls the internal method for 'review_large'.
    TDD Anchor: [AX_Dispatch]
    """
    mock_config_manager = mocker.Mock()
    mock_config_manager.get.side_effect = lambda key, default=None: {
        'action_executor.staging_dir': './.storage_hygiene_staging', # Corrected key and use default path
        'action_executor.dry_run': False # Corrected key
    }.get(key, default)

    # Mock the internal method we expect to be called *before* instance creation
    mock_review_method = mocker.patch('storage_hygiene.action_executor.ActionExecutor._review_large', return_value=None)

    mock_metadata_store = mocker.Mock() # Add mock store
    executor = ActionExecutor(config_manager=mock_config_manager, metadata_store=mock_metadata_store)

    action_details = {
        'action': 'review_large',
        'path': '/path/to/large_file.dat',
        'size': 2048 * 1024 * 1024 # Example size
    }
    actions_list = [action_details]

    executor.execute_actions({'review_large': actions_list}) # Pass dict format

    # Assert that the internal method was called with the details
    mock_review_method.assert_called_once_with(action_details, Path('./.storage_hygiene_staging'), False) # Use default path
# ... (keep existing tests)

def test_review_large_moves_file(mocker):
    """
    Test that _review_large calculates the correct path and calls move/makedirs.
    TDD Anchor: [AX_StageLarge], [AX_FileSystem]
    """
    mock_config_manager = mocker.Mock()

    # Mock file system operations
    mock_makedirs = mocker.patch('os.makedirs')
    mock_move = mocker.patch('shutil.move')
    mocker.patch('pathlib.Path.exists', return_value=False) # Simulate dest not existing

    mock_metadata_store = mocker.Mock() # Add mock store
    executor = ActionExecutor(config_manager=mock_config_manager, metadata_store=mock_metadata_store)

    staging_dir = Path('/tmp/staging')
    dry_run = False
    file_path = Path('/path/to/very/large_file.iso')
    action_details = {
        'action': 'review_large',
        'path': str(file_path),
        'size': 5 * 1024 * 1024 * 1024 # 5GB example
    }

    # Calculate expected destination
    expected_dest_dir = staging_dir / 'large_files'
    expected_dest_path = expected_dest_dir / file_path.name

    # Call the method directly
    executor._review_large(action_details, staging_dir, dry_run)

    # Assertions
    mock_makedirs.assert_called_once_with(expected_dest_dir, exist_ok=True)
    mock_move.assert_called_once_with(str(file_path), expected_dest_path)
# ... (keep existing tests)

def test_execute_actions_dispatches_review_old(mocker):
    """
    Test that execute_actions calls the internal method for 'review_old'.
    TDD Anchor: [AX_Dispatch]
    """
    mock_config_manager = mocker.Mock()
    mock_config_manager.get.side_effect = lambda key, default=None: {
        'action_executor.staging_dir': './.storage_hygiene_staging', # Corrected key and use default path
        'action_executor.dry_run': False # Corrected key
    }.get(key, default)

    # Mock the internal method we expect to be called *before* instance creation
    mock_review_method = mocker.patch('storage_hygiene.action_executor.ActionExecutor._review_old', return_value=None)

    mock_metadata_store = mocker.Mock() # Add mock store
    executor = ActionExecutor(config_manager=mock_config_manager, metadata_store=mock_metadata_store)

    action_details = {
        'action': 'review_old',
        'path': '/path/to/ancient_doc.txt',
        'last_modified': '2010-01-01T00:00:00Z' # Example date
    }
    actions_list = [action_details]

    executor.execute_actions({'review_old': actions_list}) # Pass dict format

    # Assert that the internal method was called with the details
    mock_review_method.assert_called_once_with(action_details, Path('./.storage_hygiene_staging'), False) # Use default path
# ... (keep existing tests)

def test_review_old_moves_file(mocker):
    """
    Test that _review_old calls the generic _stage_file method correctly.
    TDD Anchor: [AX_StageOld], [AX_FileSystem]
    """
    mock_config_manager = mocker.Mock()

    # Mock the generic staging method we expect to be called
    mock_stage_file = mocker.patch.object(ActionExecutor, '_stage_file', return_value=None)

    mock_metadata_store = mocker.Mock() # Add mock store
    executor = ActionExecutor(config_manager=mock_config_manager, metadata_store=mock_metadata_store)

    staging_dir = Path('/tmp/staging')
    dry_run = False
    file_path = Path('/path/to/old/archive.zip')
    action_details = {
        'action': 'review_old',
        'path': str(file_path),
        'last_modified': '2015-06-15T10:00:00Z'
    }

    # Call the method directly
    executor._review_old(action_details, staging_dir, dry_run)

    # Assertions
    mock_stage_file.assert_called_once_with(
        action_details,
        staging_dir,
        dry_run,
        'old_files', # Expected sub_dir_type
        'Staging old file' # Expected log_prefix
    )
# ... (keep existing tests)

def test_stage_file_handles_file_not_found_error(mocker):
    """
    Test that _stage_file catches FileNotFoundError during move and logs it.
    TDD Anchor: [AX_HandleErrors]
    """
    mock_config_manager = mocker.Mock()
    mock_makedirs = mocker.patch('os.makedirs')
    # Simulate FileNotFoundError during move
    mock_move = mocker.patch('shutil.move', side_effect=FileNotFoundError("File not found"))
    mock_print = mocker.patch('builtins.print')
    mocker.patch('pathlib.Path.exists', return_value=False) # Dest doesn't exist

    mock_metadata_store = mocker.Mock() # Add mock store
    executor = ActionExecutor(config_manager=mock_config_manager, metadata_store=mock_metadata_store)

    staging_dir = Path('/tmp/staging')
    dry_run = False
    file_path = Path('/path/to/nonexistent_file.txt')
    action_details = {
        'action': 'review_large', # Use any action that calls _stage_file
        'path': str(file_path),
        'size': 1024
    }
    expected_dest_path = staging_dir / 'large_files' / file_path.name

    # Call the method directly and assert that it raises the expected exception
    with pytest.raises(FileNotFoundError, match="File not found"):
        executor._stage_file(action_details, staging_dir, dry_run, 'large_files', 'Staging large file')

    # Assertions
    mock_makedirs.assert_called_once() # Make sure it tried to create the dir
    mock_move.assert_called_once_with(str(file_path), expected_dest_path) # Make sure it tried to move
    # Check if the error message was printed (it should be before the exception is raised)
    mock_print.assert_any_call(f"Error moving file {file_path} to {expected_dest_path}: File not found")