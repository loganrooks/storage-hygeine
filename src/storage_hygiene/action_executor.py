import os
import shutil
import logging
from pathlib import Path
# from .config_manager import ConfigManager # Assuming ConfigManager is in the same package

class ActionExecutor:
    """
    Executes actions based on analysis results and configuration.
    """
    def __init__(self, config_manager):
        """
        Initializes the ActionExecutor.

        Args:
            config_manager: An instance of ConfigManager (or a compatible mock).
                            TDD Anchor: [AX_Init]
        """
        self.config_manager = config_manager
        # Map action types to handler methods
        self._action_handlers = {
            'stage_duplicate': self._stage_duplicate,
            'review_large': self._review_large,
            'review_old': self._review_old,
        }
        # Placeholder for logger setup
        # self.logger = logging.getLogger(__name__)

    def execute_actions(self, actions):
        """
        Executes a list of actions.
        TDD Anchor: [AX_Execute], [AX_LoadConfig]

        Args:
            actions: A list of action dictionaries.
        """
        staging_dir = self.config_manager.get('action.staging_dir', Path('./.storage_hygiene_staging'))
        dry_run = self.config_manager.get('action.dry_run', False)
        staging_dir_path = Path(staging_dir) # Convert to Path object

        # Action loop and dispatch using handler map
        for action_details in actions:
            action_type = action_details.get('action')
            handler = self._action_handlers.get(action_type)
            if handler:
                try:
                    handler(action_details, staging_dir_path, dry_run)
                except Exception as e:
                    # Basic error logging for now
                    print(f"Error executing action {action_type} for {action_details.get('path')}: {e}")
                    # self.logger.error(f"Error executing action {action_type} for {action_details.get('path')}: {e}", exc_info=True)
            else:
                # Log unknown action type
                print(f"Unknown action type '{action_type}' encountered.")
                # self.logger.warning(f"Unknown action type '{action_type}' encountered for path {action_details.get('path')}")

    # Placeholder implementations for action methods
    def _get_staging_path(self, sub_dir_type, staging_dir, file_path_obj, file_hash=None):
        """Helper to determine the destination path within the staging directory."""
        # TDD Anchor: [AX_StagePath] - Refactored
        if sub_dir_type == 'duplicates':
            if not file_hash:
                # self.logger.error(f"Missing hash for duplicate staging path on {file_path_obj}")
                print(f"Error: Missing hash for duplicate staging path on {file_path_obj}")
                return None
            # Use first 2 chars of hash for subdirectory, then full hash
            dest_dir = staging_dir / sub_dir_type / file_hash[:2] / file_hash
        elif sub_dir_type in ['large_files', 'old_files']: # Group similar simple paths
            dest_dir = staging_dir / sub_dir_type
        else:
            # self.logger.error(f"Unknown sub_dir_type '{sub_dir_type}' for staging path calculation.")
            print(f"Error: Unknown sub_dir_type '{sub_dir_type}' for staging path calculation.")
            return None

        return dest_dir / file_path_obj.name

    def _stage_file(self, action_details, staging_dir, dry_run, sub_dir_type, log_prefix):
        """Generic method to move a file to a staging sub-directory."""
        # TDD Anchor: [AX_FileSystem] - Refactored
        file_path_str = action_details.get('path')
        file_hash = action_details.get('hash', None) # Needed for duplicates path

        if not file_path_str:
            # self.logger.error(f"Missing path in {log_prefix} action: {action_details}")
            print(f"Error: Missing path in {log_prefix} action: {action_details}")
            return

        # Hash is required only for duplicates staging path calculation
        if sub_dir_type == 'duplicates' and not file_hash:
             # self.logger.error(f"Missing hash for stage_duplicate action: {action_details}")
             print(f"Error: Missing hash for stage_duplicate action: {action_details}")
             return

        file_path_obj = Path(file_path_str)
        dest_path = self._get_staging_path(sub_dir_type, staging_dir, file_path_obj, file_hash)

        if not dest_path:
            return # Error already logged by _get_staging_path

        dest_dir = dest_path.parent

        # self.logger.info(f"{log_prefix}: {file_path_obj} -> {dest_path}")
        print(f"{log_prefix}: {file_path_obj} -> {dest_path}") # Placeholder log

        if not dry_run:
            try:
                os.makedirs(dest_dir, exist_ok=True)
                # Prevent moving if destination already exists
                if not dest_path.exists():
                    shutil.move(str(file_path_obj), dest_path)
                    # self.logger.info(f"Successfully moved {file_path_obj} to {dest_path}")
                    print(f"Successfully moved {file_path_obj} to {dest_path}") # Placeholder log
                else:
                    # self.logger.warning(f"Destination {dest_path} already exists. Skipping move for {file_path_obj}.")
                    print(f"Warning: Destination {dest_path} already exists. Skipping move for {file_path_obj}.") # Placeholder log
            except OSError as e:
                # self.logger.error(f"Error moving file {file_path_obj} to {dest_path}: {e}", exc_info=True)
                print(f"Error moving file {file_path_obj} to {dest_path}: {e}") # Placeholder log
            except Exception as e:
                # self.logger.error(f"Unexpected error staging file {file_path_obj}: {e}", exc_info=True)
                print(f"Unexpected error staging file {file_path_obj}: {e}") # Placeholder log
        else:
            # self.logger.info(f"[DRY RUN] Would move {file_path_obj} to {dest_path}")
            print(f"[DRY RUN] Would move {file_path_obj} to {dest_path}") # Placeholder log


    def _stage_duplicate(self, action_details, staging_dir, dry_run):
        """Moves a duplicate file to the staging area using the generic method."""
        # TDD Anchor: [AX_StageDup]
        self._stage_file(action_details, staging_dir, dry_run, 'duplicates', 'Staging duplicate')


    def _review_large(self, action_details, staging_dir, dry_run):
        """Moves a large file to the staging area for review using the generic method."""
        # TDD Anchor: [AX_StageLarge]
        self._stage_file(action_details, staging_dir, dry_run, 'large_files', 'Staging large file')


    def _review_old(self, action_details, staging_dir, dry_run):
        """Moves an old file to the staging area for review using the generic method."""
        # TDD Anchor: [AX_StageOld]
        self._stage_file(action_details, staging_dir, dry_run, 'old_files', 'Staging old file')

    # def _review_old(self, action_details):
    #     pass
    # def _get_staging_path(self, action_type, file_path, file_hash=None):
    #     pass