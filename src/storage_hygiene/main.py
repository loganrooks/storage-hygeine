# src/storage_hygiene/main.py
import argparse
import logging
import sys
from pathlib import Path

# Import components using the updated __init__.py
from storage_hygiene import (
    ConfigManager,
    ConfigLoadError,
    MetadataStore,
    Scanner,
    AnalysisEngine,
    ActionExecutor,
)

# Basic logging setup - explicitly use stdout
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stdout)
logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = "config.yaml" # Assuming a default config name
DEFAULT_DB_PATH = "metadata.db" # Assuming a default db name

def main():
    """Main function to orchestrate the storage hygiene workflow."""
    parser = argparse.ArgumentParser(description="Storage Hygiene System")
    parser.add_argument(
        "-c", "--config",
        type=str,
        default=DEFAULT_CONFIG_PATH,
        help=f"Path to the configuration file (default: {DEFAULT_CONFIG_PATH})"
    )
    parser.add_argument(
        "target_dirs",
        nargs='+', # Require at least one directory
        type=str,
        help="One or more target directories to scan."
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default=DEFAULT_DB_PATH,
        help=f"Path to the metadata database file (default: {DEFAULT_DB_PATH})"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run without executing any file actions."
    )
    args = parser.parse_args()

    logger.info("Starting Storage Hygiene System...")

    # --- 1. Load Configuration ---
    try:
        logger.info(f"Loading configuration from: {args.config}")
        config_manager = ConfigManager(user_config_path=args.config) # Corrected argument name
        # Determine dry_run status (CLI takes precedence)
        if args.dry_run:
            logger.info("Dry run mode enabled via CLI.")
            effective_dry_run = True
        else:
            # Get from config or default to False if not specified
            effective_dry_run = config_manager.get('action_executor.dry_run', False)

    except ConfigLoadError as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)
    except FileNotFoundError:
        logger.error(f"Configuration file not found at: {args.config}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred during configuration loading: {e}", exc_info=True)
        sys.exit(1)


    # --- 2. Initialize and Use MetadataStore ---
    db_path = args.db_path
    logger.info(f"Initializing metadata store at: {db_path}")
    try:
        # Use MetadataStore as a context manager
        with MetadataStore(db_path=db_path) as metadata_store:

            # --- 3. Run Scanner (within the 'with' block) ---
            logger.info("Initializing scanner...")
            scanner = Scanner(config_manager, metadata_store) # Pass store instance
            scan_targets = [Path(d) for d in args.target_dirs]
            logger.info(f"Scanning target directories: {', '.join(map(str, scan_targets))}")
            scan_errors = False
            for target_dir in scan_targets:
                if not target_dir.is_dir():
                    logger.warning(f"Target directory not found or is not a directory: {target_dir}. Skipping.")
                    continue
                try:
                    logger.info(f"Scanning {target_dir}...")
                    scanner.scan_directory(target_dir)
                    logger.info(f"Finished scanning {target_dir}.")
                except Exception as e:
                    logger.error(f"Error during scanning of {target_dir}: {e}", exc_info=True)
                    scan_errors = True
                    # Continue scanning other directories even if one fails
            if scan_errors:
                logger.warning("Errors occurred during scanning. Proceeding with analysis, but results may be incomplete.")
            logger.info("Scanning phase complete.")

            # --- 4. Run AnalysisEngine (within the 'with' block) ---
            logger.info("Initializing analysis engine...")
            analysis_engine = AnalysisEngine(config_manager, metadata_store)
            logger.info("Running analysis...")
            try:
                analysis_results = analysis_engine.analyze()
                action_count = sum(len(files) for files in analysis_results.values())
                logger.info(f"Analysis complete. Found {action_count} potential actions.")
                # Optional: Print summary of analysis results
                for action_type, files in analysis_results.items():
                   if files: # Only log if there are files for this action type
                       logger.info(f" - {action_type}: {len(files)} files")
            except Exception as e:
                logger.error(f"Error during analysis: {e}", exc_info=True)
                sys.exit(1) # Exit if analysis fails within the 'with' block


            # --- 5. Run ActionExecutor (within the 'with' block) ---
            if not analysis_results or all(not files for files in analysis_results.values()):
                logger.info("No actions identified by analysis. Skipping execution phase.")
            else:
                logger.info("Initializing action executor...")
                # Instantiate without dry_run, as it's handled in execute_actions
                action_executor = ActionExecutor(config_manager)
                logger.info(f"Executing actions... (Dry Run: {effective_dry_run})")
                try:
                    # Pass the effective_dry_run value as an override
                    action_executor.execute_actions(analysis_results, dry_run_override=effective_dry_run)
                    logger.info("Action execution complete.")
                except Exception as e:
                    logger.error(f"Error during action execution: {e}", exc_info=True)
                    sys.exit(1) # Exit if actions fail within the 'with' block

    # This except block catches errors from MetadataStore initialization or the 'with' block itself
    except Exception as e:
        logger.error(f"Failed to initialize or use metadata store at {db_path}: {e}", exc_info=True)
        sys.exit(1)

    logger.info("Storage Hygiene System finished successfully.")

if __name__ == "__main__":
    main()