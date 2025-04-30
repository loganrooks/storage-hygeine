import os
import shutil
import logging
from pathlib import Path
# from .config_manager import ConfigManager # Assuming ConfigManager is in the same package

class ActionExecutor:
    """
    Executes actions based on analysis results and configuration.
    """
    def __init__(self, config_manager, metadata_store):
        """
        Initializes the ActionExecutor.

        Args:
            config_manager: An instance of ConfigManager.
            metadata_store: An instance of MetadataStore.
                            TDD Anchor: [AX_Init]
        """
        self.config_manager = config_manager
        self.metadata_store = metadata_store # Store metadata_store instance
        # Map action types to handler methods
        self._action_handlers = {
            'stage_duplicate': self._stage_duplicate,
            'review_large': self._review_large,
            'review_old': self._review_old,
        }
        # Placeholder for logger setup
        # self.logger = logging.getLogger(__name__)

    def execute_actions(self, actions: dict, dry_run_override: bool | None = None):
        """
        Executes actions based on the analysis results dictionary.
        TDD Anchor: [AX_Execute], [AX_LoadConfig]

        Args:
            actions: A dictionary where keys are action types and values are lists
                     of file info dictionaries.
            dry_run_override: If True or False, overrides the dry_run setting from config.
                              If None, uses the config setting.
        """
        # Correctly indent the method body
        staging_dir = self.config_manager.get('action_executor.staging_dir', './.storage_hygiene_staging') # Match config key used in test
        # Determine final dry_run status
        if dry_run_override is not None:
            dry_run = dry_run_override
            print(f"Using dry_run override: {dry_run}") # Placeholder log
        else:
            dry_run = self.config_manager.get('action_executor.dry_run', False) # Match config key used in test
            print(f"Using dry_run from config: {dry_run}") # Placeholder log

        staging_dir_path = Path(staging_dir) # Convert to Path object
        moved_files_this_run = set() # Track files moved in this execution

        # Action loop and dispatch using handler map
        # Iterate through the dictionary provided by AnalysisEngine
        for action_type, file_list in actions.items():
            handler = self._action_handlers.get(action_type)
            if handler:
                for action_details in file_list: # Process each file for this action type
                    file_path_str = action_details.get('path')
                    if not file_path_str:
                        print(f"Warning: Skipping action {action_type} due to missing path: {action_details}")
                        # self.logger.warning(f"Skipping action {action_type} due to missing path: {action_details}")
                        continue

                    # Check if file was already moved by a previous action in this run
                    if file_path_str in moved_files_this_run:
                        print(f"Warning: File '{file_path_str}' already processed by a previous action in this run. Skipping {action_type}.")
                        # self.logger.warning(f"File '{file_path_str}' already processed by a previous action in this run. Skipping {action_type}.")
                        continue

                    try:
                        # Pass the final dry_run value to the handler
                        handler(action_details, staging_dir_path, dry_run)
                        # If handler involves a move and succeeds, add path to set
                        # Currently, all handlers call _stage_file which handles the move
                        # We rely on _stage_file raising OSError on failure, preventing this line from being reached
                        if not dry_run and action_type in ['stage_duplicate', 'review_large', 'review_old']:
                             moved_files_this_run.add(file_path_str)
                    except OSError as e: # Catch OSError specifically
                        # Log the critical file system error
                        print(f"Critical error during action {action_type} for {action_details.get('path')}: {e}")
                        # self.logger.critical(f"Critical error during action {action_type} for {action_details.get('path')}: {e}", exc_info=True)
                        raise # Re-raise OSError to halt execution
                    except Exception as e:
                        # Log other non-critical errors but continue processing other files/actions
                        print(f"Non-critical error executing action {action_type} for {action_details.get('path')}: {e}")
                        # self.logger.error(f"Non-critical error executing action {action_type} for {action_details.get('path')}: {e}", exc_info=True)
            else:
                # Log unknown action type
                print(f"Unknown action type '{action_type}' encountered.")
                # self.logger.warning(f"Unknown action type '{action_type}' encountered.") # Path is not directly available here

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
                    # Update the path in the metadata store
                    try:
                        # Use normalized old path for lookup
                        normalized_old_path = os.path.normcase(str(file_path_obj))
                        # Store normalized new path
                        normalized_new_path = os.path.normcase(str(dest_path))
                        self.metadata_store.update_file_path(old_path=normalized_old_path, new_path=normalized_new_path)
                    except Exception as db_e:
                        # self.logger.error(f"Failed to update database path for {normalized_old_path} after move: {db_e}", exc_info=True)
                        print(f"Error updating database path for {file_path_obj} after move: {db_e}") # Placeholder log
                else:
                    # self.logger.warning(f"Destination {dest_path} already exists. Skipping move for {file_path_obj}.")
                    print(f"Warning: Destination {dest_path} already exists. Skipping move for {file_path_obj}.") # Placeholder log
            except OSError as e:
                # self.logger.error(f"Error moving file {file_path_obj} to {dest_path}: {e}", exc_info=True)
                print(f"Error moving file {file_path_obj} to {dest_path}: {e}") # Placeholder log
                raise # Re-raise OSError to signal failure up the chain
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