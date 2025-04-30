# Specification Writer Specific Memory
<!-- Entries below should be added reverse chronologically (newest first) -->

## Pseudocode Library

### Pseudocode: CLI Handler - Main Orchestration
- Created: 2025-04-29 20:30:01 
- Updated: 2025-04-29 20:30:01
```pseudocode
// File: pseudocode/cli_handler.pseudo
// Component: CLI Handler (using click/typer concepts)

// --- Constants ---
ACTION_STATUS_PENDING = "PENDING_CONFIRMATION"
ACTION_STATUS_CONFIRMED = "CONFIRMED"
ACTION_STATUS_USER_REJECTED = "USER_REJECTED"

// --- Data Structures ---
// ConfigManager (see config_manager.pseudo)
// ScannerService (see scanner.pseudo)
// AnalysisEngine (see analysis_engine.pseudo)
// ActionExecutor (see action_executor.pseudo)
// DBConnection (DuckDB connection for reporting/confirmation)

// --- Module: CLIHandler ---

// Main application entry point
FUNCTION main():
    // Initialize core components (dependency injection)
    config_mgr = ConfigManager()
    // Initialize DB schema if needed (can be done here or on first use)
    initialize_database(config_mgr.get_db_path()) 
    
    // Setup output queue for scanner -> db_writer
    db_write_queue = create_multiprocessing_queue()

    // Start DB Writer process
    db_writer_proc = start_process(target=db_writer_process_loop, 
                                   args=(config_mgr.get_db_path(), db_write_queue))
    // TDD: Test DB writer process is started.

    // Initialize other services, passing dependencies
    scanner_svc = ScannerService(config_mgr, db_write_queue)
    analysis_eng = AnalysisEngine(config_mgr)
    action_exec = ActionExecutor(config_mgr)

    // Setup CLI command structure (using click/typer decorators conceptually)
    cli_app = create_cli_app()
    register_command(cli_app, "scan", handle_scan_command, scanner_svc)
    register_command(cli_app, "analyze", handle_analyze_command, analysis_eng)
    register_command(cli_app, "report", handle_report_command, config_mgr) // Needs DB access too
    register_command(cli_app, "confirm", handle_confirm_command, config_mgr) // Needs DB access too
    register_command(cli_app, "execute", handle_execute_command, action_exec)
    register_command(cli_app, "config", handle_config_command, config_mgr)
    
    TRY
        // Run the CLI application
        cli_app.run() 
    FINALLY:
        // Ensure background processes are shut down gracefully
        log_info("CLI exiting. Shutting down services...")
        scanner_svc.shutdown()
        analysis_eng.shutdown() 
        // Signal DB writer to finish
        db_write_queue.put(DB_QUEUE_SENTINEL) 
        wait_for_process_to_finish(db_writer_proc, timeout=10)
        log_info("Shutdown complete.")
        // TDD: Test scanner pool shutdown is called.
        // TDD: Test analysis pool shutdown is called.
        // TDD: Test DB writer sentinel is sent and process joined.

// --- Command Handlers ---

// Conceptual command: `hygiene scan [--path URI] [--full]`
FUNCTION handle_scan_command(scanner_service: ScannerService, path: List[String], full: Boolean):
    // path: Optional list of paths/URIs to scan (overrides config)
    // full: Flag to force a full rescan (ignore incremental checks)
    log_cli("Starting scan...")
    display_progress_bar_start("Scanning") // Use tqdm/rich progress

    TRY
        // Need a way to report progress back from workers (e.g., another queue, shared state - complex)
        // Simple approach: just show spinner until submit is done.
        scanner_service.start_scan(scan_paths=path if path else None, full_rescan=full)
        // Wait might happen here or in main depending on desired CLI behavior
        // For now, assume start_scan submits and returns quickly. Progress is tricky.
        display_progress_bar_finish() 
        log_cli_success("Scan initiated. Check logs or run reports later.")
        // TDD: Test calling scanner_service.start_scan with correct paths.
        // TDD: Test calling scanner_service.start_scan with full_rescan flag.
        // TDD: Test CLI output on successful initiation.
    CATCH Exception as e:
        display_progress_bar_finish()
        log_cli_error(f"Scan initiation failed: {e}")
        set_exit_code(1)
        // TDD: Test handling exceptions during scan initiation.

// Conceptual command: `hygiene analyze [--session ID]`
FUNCTION handle_analyze_command(analysis_engine: AnalysisEngine, session: String):
    // session: Optional scan session ID to analyze (defaults to latest?)
    log_cli("Starting analysis...")
    display_progress_bar_start("Analyzing") // Or just a spinner

    // Determine target scan_session_id (e.g., query DB for latest if session is None)
    target_session_id = session IF session ELSE get_latest_scan_session_id(analysis_engine.db_path)
    // TDD: Test getting latest session ID if none provided.
    
    IF target_session_id IS None:
         log_cli_error("No scan session found to analyze.")
         set_exit_code(1)
         RETURN

    TRY
        analysis_engine.run_analysis(target_session_id)
        display_progress_bar_finish()
        log_cli_success(f"Analysis complete for session: {target_session_id}")
        // TDD: Test calling analysis_engine.run_analysis with correct session ID.
        // TDD: Test CLI output on successful analysis.
    CATCH Exception as e:
        display_progress_bar_finish()
        log_cli_error(f"Analysis failed: {e}")
        set_exit_code(1)
        // TDD: Test handling exceptions during analysis.

// Conceptual command: `hygiene report [--category NAME] [--format FMT] [--output FILE] [--session ID]`
FUNCTION handle_report_command(config_manager: ConfigManager, category: String, format: String, output: String, session: String):
    // category: e.g., 'duplicates', 'large_files', 'rule:backup_docs'
    // format: 'table', 'list', 'csv', 'json'
    // output: File path to write to (stdout if None)
    // session: Specific scan session ID (defaults to latest?)
    log_cli(f"Generating report for category '{category}'...")
    db_conn = None
    target_session_id = session IF session ELSE get_latest_scan_session_id(config_manager.get_db_path())
    // TDD: Test getting latest session ID.

    IF target_session_id IS None:
         log_cli_error("No scan session found to report on.")
         set_exit_code(1)
         RETURN

    TRY
        db_conn = duckdb_connect(config_manager.get_db_path(), read_only=True)
        // TDD: Test successful DB connection.

        // Build query based on category
        sql_query, params = build_report_query(category, target_session_id)
        // TDD: Test building query for 'duplicates' category.
        // TDD: Test building query for 'large_files' category.
        // TDD: Test building query for specific rule name.
        // TDD: Test building query for specific analysis flag.

        results = db_conn.execute(sql_query, params).fetchall()
        // TDD: Test executing report query.

        // Format results
        formatted_output = format_report_results(results, format)
        // TDD: Test formatting as 'table'.
        // TDD: Test formatting as 'list'.
        // TDD: Test formatting as 'csv'.
        // TDD: Test formatting as 'json'.

        // Write output
        IF output:
            write_to_file(output, formatted_output)
            log_cli_success(f"Report written to: {output}")
            // TDD: Test writing report to file.
        ELSE:
            print_to_console(formatted_output)
            // TDD: Test writing report to console.

    CATCH DuckDBError as e:
        log_cli_error(f"Database error generating report: {e}")
        set_exit_code(1)
        // TDD: Test handling DB errors during reporting.
    CATCH Exception as e:
        log_cli_error(f"Failed to generate report: {e}")
        set_exit_code(1)
        // TDD: Test handling unexpected errors during reporting.
    FINALLY:
        IF db_conn IS NOT None:
            db_conn.close()

// Conceptual command: `hygiene confirm [--category NAME | --rule NAME | --file-list FILE] [--yes]`
FUNCTION handle_confirm_command(config_manager: ConfigManager, category: String, rule: String, file_list: String, yes: Boolean):
    // category/rule/file_list specify which PENDING actions to confirm. Mutually exclusive?
    // yes: Skip interactive prompts.
    log_cli("Confirming actions...")
    db_conn = None
    
    // Validate arguments (only one source allowed)
    IF count_truthy(category, rule, file_list) != 1:
        log_cli_error("Specify exactly one of --category, --rule, or --file-list.")
        set_exit_code(1)
        RETURN
    // TDD: Test validation fails if multiple sources provided.
    // TDD: Test validation fails if no source provided.

    TRY
        db_conn = duckdb_connect(config_manager.get_db_path(), read_only=False)
        // TDD: Test successful DB connection.

        // Fetch PENDING actions matching criteria
        action_ids_to_confirm = fetch_pending_action_ids(db_conn, category, rule, file_list)
        // TDD: Test fetching pending actions by category.
        // TDD: Test fetching pending actions by rule name.
        // TDD: Test fetching pending actions from file list.
        // TDD: Test returns empty list if no matching pending actions.

        IF len(action_ids_to_confirm) == 0:
            log_cli_warning("No pending actions found matching the criteria.")
            RETURN

        confirmed_count = 0
        rejected_count = 0

        IF yes: // Non-interactive confirmation
            log_cli_warning(f"Non-interactively confirming {len(action_ids_to_confirm)} actions...")
            update_action_statuses(db_conn, action_ids_to_confirm, ACTION_STATUS_CONFIRMED)
            confirmed_count = len(action_ids_to_confirm)
            // TDD: Test non-interactive confirm updates all statuses to CONFIRMED.
        ELSE: // Interactive confirmation
            // Display summary of actions
            display_confirmation_summary(db_conn, action_ids_to_confirm)
            
            // Prompt user for confirmation (overall or per item?) - Assume overall for now.
            user_confirm = prompt_user_yes_no(f"Confirm execution of {len(action_ids_to_confirm)} actions?")
            // TDD: Test interactive prompt shown.
            
            IF user_confirm:
                update_action_statuses(db_conn, action_ids_to_confirm, ACTION_STATUS_CONFIRMED)
                confirmed_count = len(action_ids_to_confirm)
                // TDD: Test interactive confirm 'yes' updates statuses to CONFIRMED.
            ELSE:
                update_action_statuses(db_conn, action_ids_to_confirm, ACTION_STATUS_USER_REJECTED)
                rejected_count = len(action_ids_to_confirm)
                log_cli_info("Actions rejected by user.")
                // TDD: Test interactive confirm 'no' updates statuses to USER_REJECTED.

        log_cli_success(f"Confirmation complete. Confirmed: {confirmed_count}, Rejected: {rejected_count}")

    CATCH DuckDBError as e:
        log_cli_error(f"Database error during confirmation: {e}")
        set_exit_code(1)
        // TDD: Test handling DB errors during confirmation.
    CATCH Exception as e:
        log_cli_error(f"Failed to confirm actions: {e}")
        set_exit_code(1)
        // TDD: Test handling unexpected errors during confirmation.
    FINALLY:
        IF db_conn IS NOT None:
            db_conn.close()

// Conceptual command: `hygiene execute`
FUNCTION handle_execute_command(action_executor: ActionExecutor):
    log_cli("Starting execution of confirmed actions...")
    display_progress_bar_start("Executing") // Need progress reporting from executor

    TRY
        // Executor handles fetching confirmed actions and updating status internally
        action_executor.execute_confirmed_actions() 
        display_progress_bar_finish()
        log_cli_success("Execution finished. Check logs for details.")
        // TDD: Test calling action_executor.execute_confirmed_actions.
        // TDD: Test CLI output on successful execution finish.
    CATCH Exception as e:
        display_progress_bar_finish()
        log_cli_error(f"Execution failed: {e}")
        set_exit_code(1)
        // TDD: Test handling exceptions during execution.

// Conceptual command: `hygiene config get KEY` | `hygiene config set KEY VALUE` | `hygiene config list` | `hygiene config edit` | `hygiene config set-credential KEY`
FUNCTION handle_config_command(config_manager: ConfigManager, action: String, key: String, value: String):
    // action: 'get', 'set', 'list', 'edit', 'set-credential'
    TRY
        IF action == "get":
            setting_value = config_manager.get_setting(key)
            print_to_console(setting_value)
            // TDD: Test 'get' retrieves and prints setting.
        ELSE IF action == "set":
            // Need type conversion for value based on key? Or assume string?
            typed_value = parse_config_value(key, value) 
            config_manager.set_setting(key, typed_value)
            config_manager.save_config() // Save after setting
            log_cli_success(f"Set '{key}' to '{typed_value}'.")
            // TDD: Test 'set' updates setting and saves config.
            // TDD: Test 'set' handles invalid value format.
        ELSE IF action == "list":
            print_to_console(format_as_yaml(config_manager.get_all_settings())) // Exclude sensitive?
            // TDD: Test 'list' prints current config.
        ELSE IF action == "edit":
            open_file_in_editor(config_manager.config_file_path)
            log_cli_info("Opened config file in editor. Reloading configuration...")
            config_manager.load_config() // Reload after edit
            // TDD: Test 'edit' opens correct file path.
            // TDD: Test config reloaded after edit (mock editor).
        ELSE IF action == "set-credential":
             // Prompt user securely for the credential value
             credential_value = prompt_user_for_secret(f"Enter value for credential '{key}':")
             IF credential_value:
                 IF config_manager.set_credential(key, credential_value):
                     log_cli_success(f"Credential '{key}' stored securely.")
                 ELSE:
                     log_cli_error(f"Failed to store credential '{key}'.")
                     set_exit_code(1)
             ELSE:
                 log_cli_warning("No credential value provided.")
             // TDD: Test 'set-credential' prompts user.
             // TDD: Test 'set-credential' calls config_manager.set_credential.
             // TDD: Test 'set-credential' handles success/failure from config_manager.
        ELSE:
            log_cli_error(f"Unknown config action: {action}")
            set_exit_code(1)
            // TDD: Test handling unknown config action.

    CATCH ConfigurationError as e:
        log_cli_error(f"Configuration error: {e}")
        set_exit_code(1)
        // TDD: Test handling ConfigurationError.
    CATCH Exception as e:
        log_cli_error(f"Failed config action '{action}': {e}")
        set_exit_code(1)
        // TDD: Test handling unexpected errors during config actions.

// --- Helper Functions ---
FUNCTION log_cli(message: String): pass // Print simple info message
FUNCTION log_cli_success(message: String): pass // Print success message (e.g., green)
FUNCTION log_cli_warning(message: String): pass // Print warning message (e.g., yellow)
FUNCTION log_cli_error(message: String): pass // Print error message (e.g., red)
FUNCTION set_exit_code(code: Integer): pass // Set process exit code

FUNCTION display_progress_bar_start(description: String): pass // Show progress bar/spinner
FUNCTION display_progress_bar_update(amount: Integer): pass // Update progress
FUNCTION display_progress_bar_finish(): pass // Hide progress bar

FUNCTION prompt_user_yes_no(message: String): Boolean // Use inquirerpy or similar
FUNCTION prompt_user_for_secret(message: String): String // Use getpass or inquirerpy password

FUNCTION build_report_query(category: String, session_id: String): Tuple[String, List]
    // Builds SQL SELECT for FileMetadata based on category/rule/flag.
    pass

FUNCTION format_report_results(results: List[Tuple], format: String): String
    // Formats DB results into table, list, csv, json. Use rich.Table etc.
    pass

FUNCTION fetch_pending_action_ids(db_conn: DBConnection, category: String, rule: String, file_list: String): List[Integer]
    // Builds query for ActionItem based on criteria, returns list of IDs.
    // If file_list, read paths from file and find corresponding file_ids first.
    pass

FUNCTION update_action_statuses(db_conn: DBConnection, action_ids: List[Integer], new_status: String):
    // Batch update ActionItem statuses.
    pass

FUNCTION display_confirmation_summary(db_conn: DBConnection, action_ids: List[Integer]):
    // Show user what actions they are about to confirm (counts per type, total size etc.)
    pass

FUNCTION get_latest_scan_session_id(db_path: String): String OR None
    // Query DB for the most recent scan_session_id.
    pass

// Other helpers: create_cli_app, register_command, count_truthy, parse_config_value, 
// open_file_in_editor, create_multiprocessing_queue, start_process, wait_for_process_to_finish etc.
```
#### TDD Anchors:
- Test DB writer process is started.
- Test scanner pool shutdown is called.
- Test analysis pool shutdown is called.
- Test DB writer sentinel is sent and process joined.
- Test calling scanner_service.start_scan with correct paths/flags.
- Test handling exceptions during scan initiation.
- Test calling analysis_engine.run_analysis with correct session ID.
- Test handling exceptions during analysis.
- Test building report queries for various categories/flags.
- Test formatting report results (table, list, csv, json).
- Test writing report to file/console.
- Test handling DB/unexpected errors during reporting.
- Test confirm argument validation.
- Test fetching pending actions by category/rule/file list.
- Test non-interactive confirm updates statuses.
- Test interactive confirm updates statuses based on user input.
- Test handling DB/unexpected errors during confirmation.
- Test calling action_executor.execute_confirmed_actions.
- Test handling exceptions during execution.
- Test config 'get', 'set', 'list', 'edit', 'set-credential' actions.
- Test handling ConfigurationError/unexpected errors during config actions.

### Pseudocode: Action Executor - Executing Actions
- Created: 2025-04-29 20:29:03
- Updated: 2025-04-29 20:29:03
```pseudocode
// File: pseudocode/action_executor.pseudo
// Component: Action Executor
// --- Constants ---
CONSTANT ACTION_STATUS_CONFIRMED = "CONFIRMED"
CONSTANT ACTION_STATUS_IN_PROGRESS = "IN_PROGRESS"
CONSTANT ACTION_STATUS_COMPLETED = "COMPLETED"
CONSTANT ACTION_STATUS_FAILED = "FAILED"
CONSTANT ACTION_STATUS_SKIPPED = "SKIPPED"

CONSTANT TEMP_DIR_PREFIX = "storage_hygiene_staging_"

// --- Data Structures ---
// ConfigManager (Provides credentials, transfer rule options - see config_manager.pseudo)
// DBConnection (DuckDB connection for R/W)
// ActionItemData (Fetched from DB: id, file_id, source_path, rule_name, action_type, target_path, ...)
// CloudClient (Abstract representation of OneDrive/GDrive SDK client)
// TransferRule (From ConfigManager, fetched by rule_name)

// --- Module: ActionExecutor ---

CLASS ActionExecutor:
    PRIVATE config_manager: ConfigManager
    PRIVATE db_path: String

    FUNCTION __init__(config_manager: ConfigManager):
        self.config_manager = config_manager
        self.db_path = config_manager.get_db_path()
        // TDD: Test initialization stores config manager and db path.

    FUNCTION execute_confirmed_actions():
        // Main entry point to process confirmed actions.
        db_conn = None
        log_info("Starting execution of confirmed actions...")
        
        actions_processed = 0
        actions_failed = 0
        
        TRY
            db_conn = duckdb_connect(self.db_path, read_only=False)
            // TDD: Test successful DB connection.

            confirmed_actions = self._fetch_confirmed_actions(db_conn)
            // TDD: Test fetching confirmed actions returns correct data/empty list.
            
            log_info(f"Found {len(confirmed_actions)} actions to execute.")

            FOR action_data IN confirmed_actions:
                success = False
                error_message = None
                final_status = ACTION_STATUS_FAILED # Default to failed unless explicitly successful or skipped
                TRY
                    // Mark action as IN_PROGRESS
                    self._update_action_status(db_conn, action_data.id, ACTION_STATUS_IN_PROGRESS)
                    // TDD: Test status updated to IN_PROGRESS before execution.

                    // Get rule details for options
                    rule = self.config_manager.get_transfer_rule_by_name(action_data.rule_name)
                    // TDD: Test fetching rule details by name.

                    // Dispatch to appropriate handler
                    handler = self._get_action_handler(action_data.action_type)
                    // TDD: Test getting correct handler for each action type.
                    
                    IF handler IS NOT None:
                        log_info(f"Executing action ID {action_data.id}: {action_data.action_type} on '{action_data.source_path}'")
                        // Execute with retry logic for relevant operations (cloud)
                        // Use tenacity decorator or similar on handler methods
                        handler(self, db_conn, action_data, rule) 
                        success = True
                        final_status = ACTION_STATUS_COMPLETED
                    ELSE:
                        error_message = f"Unsupported action type: {action_data.action_type}"
                        log_error(error_message)
                        // TDD: Test handling unsupported action type.
                
                CATCH SkipAction as e:
                     error_message = f"Action skipped: {e}"
                     log_warning(f"Action ID {action_data.id} skipped: {error_message}")
                     final_status = ACTION_STATUS_SKIPPED
                     // TDD: Test handling SkipAction sets status to SKIPPED.
                CATCH FileNotFoundError as e:
                    error_message = f"Source file not found: {e}"
                    log_error(f"Action ID {action_data.id} failed: {error_message}")
                    // TDD: Test handling FileNotFoundError during execution.
                CATCH PermissionError as e:
                     error_message = f"Permission denied: {e}"
                     log_error(f"Action ID {action_data.id} failed: {error_message}")
                     // TDD: Test handling PermissionError during execution.
                CATCH CloudAPIError as e:
                     error_message = f"Cloud API error: {e}"
                     log_error(f"Action ID {action_data.id} failed: {error_message}")
                     // TDD: Test handling CloudAPIError during execution.
                CATCH StagingError as e:
                     error_message = f"Staging area error: {e}"
                     log_error(f"Action ID {action_data.id} failed: {error_message}")
                     // TDD: Test handling StagingError during execution.
                CATCH Exception as e:
                    error_message = f"Unexpected error: {e}"
                    log_exception(f"Action ID {action_data.id} failed unexpectedly.") // Log full traceback
                    // TDD: Test handling unexpected errors during execution.
                
                // Update final status
                self._update_action_status(db_conn, action_data.id, final_status, error_message)
                actions_processed += 1
                IF final_status == ACTION_STATUS_FAILED:
                    actions_failed += 1
                // TDD: Test status updated to COMPLETED on success.
                // TDD: Test status updated to FAILED on error, message recorded.
                // TDD: Test status updated to SKIPPED on skip.

            log_info(f"Action execution finished. Processed: {actions_processed}, Failed: {actions_failed}.")

        CATCH DuckDBError as e:
            log_error("Database error during action execution: " + str(e))
            // TDD: Test handling DB errors during execution run.
        CATCH Exception as e:
            log_error("Unexpected error during action execution: " + str(e))
            // TDD: Test handling unexpected errors during execution run.
        FINALLY:
            IF db_conn IS NOT None:
                db_conn.close()
            // TDD: Test DB connection closed on success/failure.

    // --- Private Helper Methods ---

    FUNCTION _fetch_confirmed_actions(db_conn: DBConnection): List[ActionItemData]
        // Fetches actions with status 'CONFIRMED' and joins with FileMetadata for source_path
        sql = """
            SELECT ai.*, fm.full_path as source_path 
            FROM ActionItem ai 
            JOIN FileMetadata fm ON ai.file_id = fm.id 
            WHERE ai.status = ?
            ORDER BY ai.suggestion_time -- Process in order suggested? Or by rule?
        """
        results = db_conn.execute(sql, [ACTION_STATUS_CONFIRMED]).fetchall()
        // Convert results to list of ActionItemData objects/dicts
        RETURN parse_action_item_results(results) 

    FUNCTION _update_action_status(db_conn: DBConnection, action_id: Integer, status: String, message: String = None):
        // Updates the status and optionally the result_message and execution_time
        current_time = get_current_time()
        sql = """
            UPDATE ActionItem 
            SET status = ?, result_message = ?, execution_time = ?
            WHERE id = ?
        """
        db_conn.execute(sql, [status, message, current_time, action_id])
        db_conn.commit()
        // TDD: Test updating status works correctly.
        // TDD: Test updating status and message works correctly.

    FUNCTION _get_action_handler(action_type: String): Function OR None
        handlers = {
            "DELETE": self._handle_delete,
            "MOVE_TRASH": self._handle_move_trash,
            "COPY_LOCAL": self._handle_copy_local,
            "MOVE_LOCAL": self._handle_move_local,
            "COPY_CLOUD": self._handle_copy_cloud,
            "MOVE_CLOUD": self._handle_move_cloud,
            // Add more handlers as needed
        }
        RETURN handlers.get(action_type)

    // --- Action Handlers (Apply retry logic via decorators where appropriate, e.g., cloud ops) ---

    // @retry(wait=exponential_backoff(...), stop=stop_after_attempt(3), retry=retry_if_exception_type(IOError)) // Example retry
    FUNCTION _handle_delete(self, db_conn: DBConnection, action: ActionItemData, rule: TransferRule):
        log_debug(f"Deleting file: {action.source_path}")
        delete_local_file_or_directory(action.source_path) // Use os.remove or os.rmdir/shutil.rmtree
        // TDD: Test deleting a file works.
        // TDD: Test deleting a directory works.
        // TDD: Test raises FileNotFoundError if source missing.
        // TDD: Test raises PermissionError if permissions insufficient.

    // @retry(...) // Less likely needed for trash, but maybe for specific OS issues
    FUNCTION _handle_move_trash(self, db_conn: DBConnection, action: ActionItemData, rule: TransferRule):
        log_debug(f"Moving to trash: {action.source_path}")
        send_to_trash(action.source_path) // Use send2trash library
        // TDD: Test moving file to trash works.
        // TDD: Test moving directory to trash works.
        // TDD: Test raises TrashPermissionError if applicable.

    // @retry(...) // For potential network drive issues?
    FUNCTION _handle_copy_local(self, db_conn: DBConnection, action: ActionItemData, rule: TransferRule):
        log_debug(f"Copying local: {action.source_path} -> {action.target_path}")
        target_path = self._prepare_target_path(action.source_path, action.target_path, rule)
        copy_local_file_with_metadata(action.source_path, target_path) // Use shutil.copy2
        // TDD: Test copying file works, preserves metadata.
        // TDD: Test copying directory works recursively.
        // TDD: Test conflict resolution (skip/rename/overwrite).
        // TDD: Test raises error if target dir doesn't exist and cannot be created.

    // @retry(...) // For potential network drive issues?
    FUNCTION _handle_move_local(self, db_conn: DBConnection, action: ActionItemData, rule: TransferRule):
        log_debug(f"Moving local: {action.source_path} -> {action.target_path}")
        target_path = self._prepare_target_path(action.source_path, action.target_path, rule)
        move_local_file_or_directory(action.source_path, target_path) // Use shutil.move
        // TDD: Test moving file works.
        // TDD: Test moving directory works.
        // TDD: Test conflict resolution (shutil.move might handle some cases).

    @retry(wait=exponential_backoff(...), stop=stop_after_attempt(3), retry=retry_if_exception_type(CloudAPIError))
    FUNCTION _handle_copy_cloud(self, db_conn: DBConnection, action: ActionItemData, rule: TransferRule):
        log_debug(f"Copying to/from/between cloud: {action.source_path} -> {action.target_path}")
        source_is_cloud, source_provider, source_item_path = parse_uri(action.source_path)
        target_is_cloud, target_provider, target_item_path = parse_uri(action.target_path)

        source_client = get_cloud_client(source_provider, self.config_manager) IF source_is_cloud ELSE None
        target_client = get_cloud_client(target_provider, self.config_manager) IF target_is_cloud ELSE None
        // TDD: Test getting source/target clients correctly.

        temp_dir = None
        local_stage_path = None
        
        TRY
            // Determine transfer path and if staging is needed
            IF source_is_cloud AND target_is_cloud AND source_provider != target_provider: // Cloud-to-Cloud
                temp_dir = create_temporary_directory(prefix=TEMP_DIR_PREFIX)
                local_stage_path = temp_dir.path / get_filename_from_path(source_item_path)
                log_debug(f"Staging cloud-to-cloud via {local_stage_path}")
                // TDD: Test cloud-to-cloud uses staging.
                
                // 1. Download from source cloud to stage
                check_disk_space(temp_dir.path, source_client.get_item_size(source_item_path)) // Estimate needed space
                source_client.download_file(source_item_path, local_stage_path)
                // TDD: Test download to stage successful.
                // TDD: Test download handles CloudAPIError.

                // 2. Upload from stage to target cloud
                target_final_path = self._prepare_cloud_target_path(target_client, target_item_path, local_stage_path, rule)
                target_client.upload_file(local_stage_path, target_final_path)
                // TDD: Test upload from stage successful.
                // TDD: Test upload handles CloudAPIError.
                // TDD: Test cloud conflict resolution (skip/rename/overwrite via API if possible, or pre-check).

            ELSE IF source_is_cloud AND NOT target_is_cloud: // Cloud-to-Local
                local_stage_path = self._prepare_target_path(action.source_path, action.target_path, rule)
                log_debug(f"Downloading cloud-to-local: {action.source_path} -> {local_stage_path}")
                // TDD: Test cloud-to-local prepares target path.
                check_disk_space(Path(local_stage_path).parent, source_client.get_item_size(source_item_path))
                source_client.download_file(source_item_path, local_stage_path)
                // TDD: Test download to local successful.

            ELSE IF NOT source_is_cloud AND target_is_cloud: // Local-to-Cloud
                local_source_path = action.source_path
                log_debug(f"Uploading local-to-cloud: {local_source_path} -> {action.target_path}")
                // TDD: Test local-to-cloud prepares target path.
                target_final_path = self._prepare_cloud_target_path(target_client, target_item_path, local_source_path, rule)
                target_client.upload_file(local_source_path, target_final_path)
                // TDD: Test upload from local successful.
            
            ELSE: // Should have been handled by _handle_copy_local
                 raise ExecutionError("Invalid state: Cloud copy handler called for local-to-local.")

        FINALLY:
            // Clean up temporary staging directory
            IF temp_dir IS NOT None:
                cleanup_temporary_directory(temp_dir)
                // TDD: Test staging directory is cleaned up.

    @retry(wait=exponential_backoff(...), stop=stop_after_attempt(3), retry=retry_if_exception_type(CloudAPIError))
    FUNCTION _handle_move_cloud(self, db_conn: DBConnection, action: ActionItemData, rule: TransferRule):
        log_debug(f"Moving to/from/between cloud: {action.source_path} -> {action.target_path}")
        // Similar logic to _handle_copy_cloud, but includes deleting the source *after* successful transfer.
        
        source_is_cloud, source_provider, source_item_path = parse_uri(action.source_path)
        target_is_cloud, target_provider, target_item_path = parse_uri(action.target_path)
        source_client = get_cloud_client(source_provider, self.config_manager) IF source_is_cloud ELSE None
        
        // Check if cloud provider supports native server-side move/rename first
        IF source_is_cloud AND target_is_cloud AND source_provider == target_provider:
            IF source_client.supports_move():
                 log_debug(f"Attempting native cloud move: {action.source_path} -> {action.target_path}")
                 target_final_path = self._prepare_cloud_target_path(source_client, target_item_path, source_item_path, rule) // Check target exists for conflict
                 source_client.move_item(source_item_path, target_final_path)
                 log_info("Native cloud move successful.")
                 RETURN // Skip copy/delete logic
                 // TDD: Test native cloud move successful.
                 // TDD: Test native cloud move conflict handling.
            ELSE:
                 log_debug("Native cloud move not supported, proceeding with copy+delete.")

        // Perform copy operation (leverages _handle_copy_cloud logic or similar)
        // Need to ensure copy doesn't raise SkipAction if we intend to delete source
        copy_rule_options = rule.options.copy()
        copy_rule_options['conflict_resolution'] = 'overwrite' # Or handle differently? Ensure target is clear.
        copy_rule = TransferRule(name=rule.name, ..., options=copy_rule_options) # Create modified rule for copy part
        
        self._handle_copy_cloud(db_conn, action, copy_rule) # Use modified rule for copy
        // TDD: Test copy part of move successful.

        // If copy was successful, delete the source
        log_debug(f"Copy successful, deleting source: {action.source_path}")
        IF source_is_cloud:
            // Add retry logic to delete as well
            source_client.delete_item(source_item_path)
            // TDD: Test cloud source deleted after successful copy.
            // TDD: Test handling errors during cloud source deletion.
        ELSE:
            // Add retry logic? Less critical for local delete maybe.
            delete_local_file_or_directory(action.source_path)
            // TDD: Test local source deleted after successful copy.
            // TDD: Test handling errors during local source deletion.

    FUNCTION _prepare_target_path(self, source_path: String, target_dir: String, rule: TransferRule): String
        // Creates target directory if needed. Handles conflicts based on rule options. Returns final target path.
        filename = get_filename_from_path(source_path)
        target_path = Path(target_dir) / filename
        
        ensure_directory_exists(Path(target_dir))
        // TDD: Test target directory created if not exists.

        IF target_path.exists():
            conflict_option = rule.options.get("conflict_resolution", "skip") // Default to skip
            // TDD: Test default conflict resolution is skip.
            IF conflict_option == "skip":
                log_warning(f"Target exists, skipping: {target_path}")
                raise SkipAction(f"Target file exists: {target_path}") 
                // TDD: Test skip option raises SkipAction.
            ELSE IF conflict_option == "rename":
                target_path = generate_unique_filename(target_path)
                log_info(f"Target exists, renaming to: {target_path}")
                // TDD: Test rename option generates unique name.
            ELSE IF conflict_option == "overwrite":
                log_warning(f"Target exists, overwriting: {target_path}")
                // TDD: Test overwrite option proceeds.
            ELSE: // Unknown option, treat as skip
                 log_warning(f"Unknown conflict option '{conflict_option}', skipping: {target_path}")
                 raise SkipAction(f"Target file exists: {target_path}")

        RETURN str(target_path)

    FUNCTION _prepare_cloud_target_path(self, cloud_client: CloudClient, target_item_path: String, source_local_path: String, rule: TransferRule): String
        // Checks for conflicts in cloud storage based on rule options. Returns final target path.
        // May involve listing target folder, similar logic to _prepare_target_path.
        // Cloud APIs might offer options for rename/overwrite on upload.
        // TDD: Test cloud target path preparation.
        // TDD: Test cloud conflict check (skip/rename/overwrite).
        pass

// --- Helper Functions ---
FUNCTION parse_action_item_results(rows: List[Tuple]): List[ActionItemData]
    // Convert DB rows to ActionItemData objects/dicts
    pass

FUNCTION get_cloud_client(provider_type: String, config_manager: ConfigManager): CloudClient OR None
    // Copied from scanner.pseudo - should be shared utility
    pass

FUNCTION parse_uri(uri: String): Tuple[Boolean, String, String]
    // Parses "onedrive:/path/file" into (True, "onedrive", "/path/file")
    // Parses "/local/path/file" into (False, None, "/local/path/file")
    pass

FUNCTION ensure_directory_exists(dir_path: Path):
    // Copied from config_manager.pseudo - should be shared utility
    pass

FUNCTION check_disk_space(directory: Path, required_bytes: Integer):
    // Checks if directory's filesystem has enough free space. Raises StagingError if not.
    // TDD: Test raises error if insufficient space.
    // TDD: Test passes if sufficient space.
    pass
    
FUNCTION create_temporary_directory(prefix: String): TempDirectoryObject
    // Uses tempfile.TemporaryDirectory
    pass

FUNCTION cleanup_temporary_directory(temp_dir: TempDirectoryObject):
    // Calls temp_dir.cleanup()
    pass

// Other helpers: delete_local_file_or_directory, send_to_trash, copy_local_file_with_metadata, 
// move_local_file_or_directory, get_filename_from_path, generate_unique_filename etc.

// --- Exceptions ---
CLASS ExecutionError(Exception): pass
CLASS CloudAPIError(Exception): pass // Copied from scanner.pseudo
CLASS StagingError(Exception): pass
CLASS SkipAction(Exception): pass // Used for graceful skipping due to conflicts etc.
```
#### TDD Anchors:
- Test initialization stores config manager and db path.
- Test successful DB connection.
- Test fetching confirmed actions returns correct data/empty list.
- Test status updated to IN_PROGRESS before execution.
- Test fetching rule details by name.
- Test getting correct handler for each action type.
- Test handling unsupported action type.
- Test handling SkipAction sets status to SKIPPED.
- Test handling FileNotFoundError/PermissionError/CloudAPIError/StagingError/unexpected errors.
- Test status updated to COMPLETED/FAILED/SKIPPED correctly.
- Test DB connection closed on success/failure.
- Test updating status/message works correctly.
- Test deleting file/directory.
- Test moving file/directory to trash.
- Test copying local file/directory, preserves metadata.
- Test moving local file/directory.
- Test conflict resolution (skip/rename/overwrite) for local operations.
- Test getting source/target cloud clients.
- Test cloud-to-cloud uses staging.
- Test download to stage successful/handles errors.
- Test upload from stage successful/handles errors.
- Test cloud conflict resolution.
- Test cloud-to-local prepares target path/downloads successfully.
- Test local-to-cloud prepares target path/uploads successfully.
- Test staging directory is cleaned up.
- Test native cloud move successful/handles conflicts.
- Test copy part of cloud move successful.
- Test cloud/local source deleted after successful move.
- Test target directory created if not exists.
- Test rename option generates unique name.
- Test cloud target path preparation/conflict check.
- Test raises error if insufficient disk space for staging.

### Pseudocode: Analysis Engine - Applying Rules
- Created: 2025-04-29 20:27:52
- Updated: 2025-04-29 20:27:52
```pseudocode
// File: pseudocode/analysis_engine.pseudo
// Component: Analysis Engine
// --- Constants ---
CONSTANT ACTION_ITEM_STATUS_PENDING = "PENDING_CONFIRMATION"
CONSTANT SIMILARITY_POOL_WORKERS = calculate_optimal_workers() // Or a fixed number

// --- Data Structures ---
// ConfigManager (Provides analysis rules, transfer rules - see config_manager.pseudo)
// DBConnection (DuckDB connection for R/W)
// ProcessPoolExecutor (For CPU-bound tasks like similarity hashing/checks)
// AnalysisRuleConfig (From ConfigManager)
// TransferRule (From ConfigManager)

// --- Module: AnalysisEngine ---

CLASS AnalysisEngine:
    PRIVATE config_manager: ConfigManager
    PRIVATE db_path: String
    PRIVATE analysis_pool: ProcessPoolExecutor // For similarity/corruption checks

    FUNCTION __init__(config_manager: ConfigManager):
        self.config_manager = config_manager
        self.db_path = config_manager.get_db_path()
        self.analysis_pool = ProcessPoolExecutor(max_workers=SIMILARITY_POOL_WORKERS)
        // TDD: Test pool initialization.

    FUNCTION run_analysis(scan_session_id: String):
        // Main entry point to run all enabled analysis steps.
        db_conn = None
        log_info("Starting analysis for scan session: " + scan_session_id)
        
        TRY
            db_conn = duckdb_connect(self.db_path, read_only=False)
            // TDD: Test successful DB connection.

            analysis_rules = self.config_manager.get_analysis_rules()
            transfer_rules = self.config_manager.get_transfer_rules()

            // --- Run Analysis Steps ---
            // Order might matter (e.g., find duplicates before suggesting actions)
            
            IF analysis_rules.get("duplicates", {}).get("enabled", False):
                self._find_duplicates(db_conn, scan_session_id)
                // TDD: Test duplicate finding is called if enabled.

            // Apply rules based on simple attributes (size, age, type, patterns)
            self._apply_attribute_rules(db_conn, scan_session_id, analysis_rules)
            // TDD: Test attribute rules application.

            IF analysis_rules.get("similarity", {}).get("enabled", False):
                 self._find_similar_files(db_conn, scan_session_id, analysis_rules.get("similarity"))
                 // TDD: Test similarity finding is called if enabled.

            IF analysis_rules.get("corruption", {}).get("enabled", False):
                 self._check_corruption(db_conn, scan_session_id, analysis_rules.get("corruption"))
                 // TDD: Test corruption checking is called if enabled.

            IF analysis_rules.get("disorganization", {}).get("enabled", False):
                 self._calculate_metrics(db_conn, scan_session_id, analysis_rules.get("disorganization"))
                 // TDD: Test disorganization metrics calculation is called if enabled.

            // Match transfer rules AFTER other analysis flags are set
            self._match_transfer_rules(db_conn, scan_session_id, transfer_rules)
            // TDD: Test transfer rule matching.

            // (Optional Post-MVP) Call AI Assistant if enabled
            // IF analysis_rules.get("ai_suggestions", {}).get("enabled", False):
            //     self._get_ai_suggestions(db_conn, scan_session_id)

            log_info("Analysis completed for scan session: " + scan_session_id)

        CATCH DuckDBError as e:
            log_error("Database error during analysis: " + str(e))
            // TDD: Test handling DB errors during analysis run.
        CATCH Exception as e:
            log_error("Unexpected error during analysis: " + str(e))
            // TDD: Test handling unexpected errors during analysis run.
        FINALLY:
            IF db_conn IS NOT None:
                db_conn.close()
            // TDD: Test DB connection is closed on success/failure.

    FUNCTION shutdown():
        log_info("Shutting down analysis process pool...")
        self.analysis_pool.shutdown(wait=True)
        log_info("Analysis process pool shut down.")
        // TDD: Test shutdown waits for pool completion.

    // --- Private Analysis Methods ---

    FUNCTION _find_duplicates(db_conn: DBConnection, scan_session_id: String):
        log_info("Finding exact duplicates...")
        TRY
            // Find hashes with more than one file
            sql_find_dup_hashes = """
                SELECT sha256_hash 
                FROM FileMetadata 
                WHERE sha256_hash IS NOT NULL AND scan_session_id = ?
                GROUP BY sha256_hash 
                HAVING COUNT(*) > 1
            """
            duplicate_hashes = db_conn.execute(sql_find_dup_hashes, [scan_session_id]).fetchall()
            // TDD: Test query finds duplicate hashes correctly.
            // TDD: Test query handles no duplicates found.

            IF len(duplicate_hashes) > 0:
                hash_list_placeholder = create_sql_placeholder_list(len(duplicate_hashes))
                
                // Flag all files matching these hashes
                sql_flag_duplicates = f"""
                    UPDATE FileMetadata 
                    SET analysis_flags = list_append_unique(analysis_flags, 'duplicate')
                    WHERE sha256_hash IN ({hash_list_placeholder}) AND scan_session_id = ?
                """
                params = [h[0] for h in duplicate_hashes] + [scan_session_id]
                db_conn.execute(sql_flag_duplicates, params)
                db_conn.commit()
                log_info(f"Flagged files for {len(duplicate_hashes)} duplicate hashes.")
                // TDD: Test update query flags correct files.
                // TDD: Test list_append_unique adds flag without duplication.
            ELSE:
                log_info("No exact duplicates found.")

        CATCH DuckDBError as e:
            log_error("Error finding duplicates: " + str(e))
            db_conn.rollback()
            // TDD: Test handling DB error during duplicate finding.

    FUNCTION _apply_attribute_rules(db_conn: DBConnection, scan_session_id: String, rules: Dict):
        log_info("Applying attribute-based analysis rules...")
        // Example for 'large_files' rule
        IF rules.get("large_files", {}).get("enabled", False):
            threshold_mb = rules["large_files"].get("threshold_mb", 1024) // Default 1GB
            threshold_bytes = threshold_mb * 1024 * 1024
            TRY
                sql = """
                    UPDATE FileMetadata 
                    SET analysis_flags = list_append_unique(analysis_flags, 'large_file')
                    WHERE size_bytes >= ? AND is_directory = FALSE AND scan_session_id = ?
                """
                db_conn.execute(sql, [threshold_bytes, scan_session_id])
                db_conn.commit()
                log_info(f"Applied 'large_file' rule (threshold: {threshold_mb} MB).")
                // TDD: Test large file rule flags correct files.
                // TDD: Test large file rule ignores directories.
            CATCH DuckDBError as e:
                log_error("Error applying 'large_file' rule: " + str(e))
                db_conn.rollback()
                // TDD: Test handling DB error during large file rule.

        // Example for 'old_files' rule
        IF rules.get("old_files", {}).get("enabled", False):
            days_threshold = rules["old_files"].get("days_threshold", 365)
            cutoff_date = calculate_cutoff_date(days_threshold) // Current date - threshold
            date_column = rules["old_files"].get("date_field", "modified_time") // Or 'accessed_time', 'created_time'
            IF date_column NOT IN ["modified_time", "accessed_time", "created_time"]:
                 date_column = "modified_time" // Safe default
            TRY:
                sql = f"""
                    UPDATE FileMetadata 
                    SET analysis_flags = list_append_unique(analysis_flags, 'old_file')
                    WHERE {date_column} < ? AND is_directory = FALSE AND scan_session_id = ? 
                """
                db_conn.execute(sql, [cutoff_date, scan_session_id])
                db_conn.commit()
                log_info(f"Applied 'old_file' rule (threshold: {days_threshold} days based on {date_column}).")
                // TDD: Test old file rule flags correct files based on mtime.
                // TDD: Test old file rule flags correct files based on atime.
                // TDD: Test old file rule ignores directories.
            CATCH DuckDBError as e:
                log_error("Error applying 'old_file' rule: " + str(e))
                db_conn.rollback()
                // TDD: Test handling DB error during old file rule.

        // Add logic for other attribute rules (temp files, zero-byte, empty folders, etc.)
        // Use SQL UPDATE statements with appropriate WHERE clauses based on config.
        // TDD: Test temp file pattern matching rule.
        // TDD: Test zero-byte file rule.
        // TDD: Test empty folder rule (might need separate query).

    FUNCTION _find_similar_files(db_conn: DBConnection, scan_session_id: String, similarity_config: Dict):
        log_info("Finding similar files...")
        // 1. Identify candidate files (e.g., by MIME type for specific hashers)
        // 2. Dispatch hash calculation tasks to self.analysis_pool
        // 3. Collect results (file_id, similarity_hash_type, similarity_hash_value)
        // 4. Update FileMetadata table with similarity hashes
        // 5. Group files by similarity hash
        // 6. Apply prioritization within groups (optional)
        // 7. Update FileMetadata table with similarity_group_id and flags (e.g., 'similar_low_priority')

        // Example: Image similarity using pHash
        image_mime_types = ["image/jpeg", "image/png", ...] // Get from config?
        phash_threshold = similarity_config.get("phash_threshold", 8) // Hamming distance threshold

        TRY:
            // Get image files that haven't been hashed yet
            sql_get_images = """
                SELECT id, full_path 
                FROM FileMetadata 
                WHERE mime_type IN (?, ?, ...) AND similarity_hash IS NULL AND is_directory = FALSE AND scan_session_id = ?
            """ 
            // TDD: Test query selects correct candidate image files.
            image_files = db_conn.execute(sql_get_images, image_mime_types + [scan_session_id]).fetchall()

            // Dispatch pHash calculation tasks
            futures = {}
            FOR file_id, file_path IN image_files:
                 future = self.analysis_pool.submit(calculate_phash_task, file_path) // Needs error handling inside task
                 futures[future] = file_id
                 // TDD: Test submitting pHash task.

            // Collect results and update DB
            phash_results = [] // List of (file_id, phash_value)
            FOR future IN wait_for_completed_futures(futures):
                file_id = futures[future]
                TRY:
                    phash_value = future.result()
                    IF phash_value IS NOT None:
                        phash_results.append((file_id, "phash:" + phash_value))
                        // TDD: Test collecting valid pHash result.
                CATCH Exception as e:
                    log_warning(f"pHash calculation failed for file_id {file_id}: {e}")
                    // Flag file with error?
                    // TDD: Test handling failed pHash task.
            
            // Batch update similarity_hash in DB
            IF len(phash_results) > 0:
                 update_similarity_hashes(db_conn, phash_results)
                 // TDD: Test batch update of similarity hashes.

            // Group by pHash and assign group IDs (more complex SQL or Python logic)
            // Example: Find pairs within threshold using Python (can be slow for many images)
            // OR use specialized DB extensions if available (e.g., for vector similarity)
            // OR approximate grouping
            
            // Simplified grouping example (find exact pHash matches first)
            sql_find_phash_groups = """
                SELECT similarity_hash, list(id) as file_ids
                FROM FileMetadata
                WHERE similarity_hash LIKE 'phash:%' AND scan_session_id = ?
                GROUP BY similarity_hash
                HAVING COUNT(*) > 1
            """
            // TDD: Test finding exact pHash match groups.
            groups = db_conn.execute(sql_find_phash_groups, [scan_session_id]).fetchall()

            // Assign group IDs and potentially prioritize
            group_updates = [] // List of (group_id, file_id)
            priority_updates = [] // List of (flag, file_id)
            FOR phash, file_ids IN groups:
                 group_id = "sim_phash_" + generate_short_uuid()
                 prioritized_ids = apply_similarity_prioritization(db_conn, file_ids, similarity_config) // Returns list of file_ids to keep
                 // TDD: Test prioritization logic selects correct files based on rules (resolution, size etc.).
                 FOR file_id IN file_ids:
                     group_updates.append((group_id, file_id))
                     IF file_id NOT IN prioritized_ids:
                          priority_updates.append(('similar_low_priority', file_id))
                          // TDD: Test non-prioritized files get flagged.

            // Batch update group IDs and priority flags
            update_similarity_groups(db_conn, group_updates)
            update_analysis_flags(db_conn, priority_updates)
            // TDD: Test batch update of group IDs.
            // TDD: Test batch update of priority flags.

            log_info("Similarity analysis (pHash) completed.")

        CATCH DuckDBError as e:
            log_error("DB error during similarity analysis: " + str(e))
            db_conn.rollback()
            // TDD: Test handling DB errors during similarity analysis.
        CATCH Exception as e:
            log_error("Unexpected error during similarity analysis: " + str(e))
            // TDD: Test handling unexpected errors.

        // Repeat similar logic for other similarity types (fuzzy hash, acoustic fingerprint) based on config and MIME types.

    FUNCTION _check_corruption(db_conn: DBConnection, scan_session_id: String, corruption_config: Dict):
        log_info("Checking for file corruption...")
        // Implement multi-level checks based on corruption_config
        
        // Level 1: Header/Magic Number/Basic Structure (Fast checks)
        IF corruption_config.get("level1_enabled", True):
            // Example: Check zip files
            sql_get_zips = "SELECT id, full_path FROM FileMetadata WHERE mime_type = 'application/zip' AND scan_session_id = ?"
            zip_files = db_conn.execute(sql_get_zips, [scan_session_id]).fetchall()
            // TDD: Test query selects zip files.
            
            futures = {}
            FOR file_id, file_path IN zip_files:
                 future = self.analysis_pool.submit(check_zip_structure_task, file_path)
                 futures[future] = file_id
                 // TDD: Test submitting zip check task.

            error_flags = [] // List of ('corrupt_structure_basic', file_id)
            FOR future IN wait_for_completed_futures(futures):
                 file_id = futures[future]
                 TRY:
                     is_corrupt = future.result()
                     IF is_corrupt:
                          error_flags.append(('corrupt_structure_basic', file_id))
                          // TDD: Test collecting zip corruption result.
                 CATCH Exception as e:
                      log_warning(f"Zip check failed for file_id {file_id}: {e}")
                      error_flags.append(('corruption_check_error', file_id))
                      // TDD: Test handling failed zip check task.
            
            update_analysis_flags(db_conn, error_flags)
            // TDD: Test updating basic corruption flags.

            // Add similar logic for python-magic, PyPDF2 basic checks.
            // TDD: Test header check task.
            // TDD: Test basic PDF check task.

        // Level 2: Full Structure (Slower, Optional)
        IF corruption_config.get("level2_enabled", False):
             // Example: Read all PDF pages
             // Submit tasks to pool, collect results, update 'corrupt_structure_full' flag.
             // TDD: Test submitting full PDF check task.
             // TDD: Test collecting full PDF corruption result.
             pass

        // Level 3: Media Sampling (Slowest, Optional, External Dependency)
        IF corruption_config.get("level3_enabled", False):
             // Example: Use ffmpeg via subprocess
             // Submit tasks to pool, collect results, update 'corrupt_content_sample' flag.
             // TDD: Test submitting ffmpeg check task.
             // TDD: Test collecting ffmpeg corruption result.
             pass
             
        log_info("Corruption checks completed.")


    FUNCTION _calculate_metrics(db_conn: DBConnection, scan_session_id: String, metrics_config: Dict):
        log_info("Calculating disorganization metrics...")
        // Implement SQL queries or data processing logic to calculate metrics defined in Arch Report 3.
        // Example: Root File Ratio
        // total_files = db_conn.execute("SELECT COUNT(*) FROM FileMetadata WHERE is_directory=FALSE AND scan_session_id=?", [scan_session_id]).fetchone()[0]
        // root_files = db_conn.execute("SELECT COUNT(*) FROM FileMetadata WHERE is_directory=FALSE AND scan_session_id=? AND directory_depth(full_path) = 0", [scan_session_id]).fetchone()[0] // Needs directory_depth function or path parsing
        // Store results somewhere? Or just report via CLI? Architecture report implies flags.
        // Update FileMetadata with flags like 'metric_high_root_ratio', 'metric_deep_folders' etc. based on thresholds.
        // TDD: Test root file ratio calculation.
        // TDD: Test average folder depth calculation.
        // TDD: Test flagging based on metric thresholds.
        pass

    FUNCTION _match_transfer_rules(db_conn: DBConnection, scan_session_id: String, transfer_rules: List[TransferRule]):
        log_info("Matching files against transfer rules...")
        IF not transfer_rules:
            log_info("No transfer rules defined.")
            RETURN

        FOR rule IN transfer_rules:
            log_debug(f"Processing transfer rule: {rule.name}")
            TRY
                // Build SQL WHERE clause based on rule.source and rule.filters
                where_clause, params = build_sql_filter(rule, scan_session_id)
                // TDD: Test building WHERE clause for path source.
                // TDD: Test building WHERE clause for category source.
                // TDD: Test building WHERE clause with name pattern filter.
                // TDD: Test building WHERE clause with size filter.
                // TDD: Test building WHERE clause with date filter.
                // TDD: Test building WHERE clause with flag filter (has_flag, not_has_flag).
                // TDD: Test combining multiple filters correctly (AND logic).

                // Construct INSERT statement for ActionItem
                sql_insert_action = f"""
                    INSERT INTO ActionItem (id, file_id, rule_name, action_type, target_path, status, suggestion_time)
                    SELECT 
                        generate_action_id(), -- Need a way to generate unique IDs
                        fm.id, 
                        ?, -- rule.name
                        ?, -- rule.action_type
                        ?, -- rule.destination
                        ?, -- ACTION_ITEM_STATUS_PENDING
                        ?  -- current_time
                    FROM FileMetadata fm
                    WHERE {where_clause}
                      -- Optional: Ensure no pending/confirmed action already exists for this file?
                      AND NOT EXISTS (SELECT 1 FROM ActionItem ai WHERE ai.file_id = fm.id AND ai.status IN ('PENDING_CONFIRMATION', 'CONFIRMED', 'IN_PROGRESS')) 
                """
                insert_params = [rule.name, rule.action_type, rule.destination, ACTION_ITEM_STATUS_PENDING, get_current_time()] + params
                
                result = db_conn.execute(sql_insert_action, insert_params)
                db_conn.commit()
                log_info(f"Rule '{rule.name}': Generated {result.rowcount} action items.") // Check actual API for rowcount
                // TDD: Test INSERT statement creates correct ActionItem records.
                // TDD: Test rule matching ignores files with existing pending/confirmed actions.

            CATCH DuckDBError as e:
                log_error(f"DB error processing rule '{rule.name}': {e}")
                db_conn.rollback()
                // TDD: Test handling DB errors during rule matching.
            CATCH Exception as e:
                log_error(f"Unexpected error processing rule '{rule.name}': {e}")
                // TDD: Test handling unexpected errors during rule matching.

// --- Helper Functions ---
FUNCTION calculate_phash_task(file_path: String): String OR None
    // Worker task: Calculate perceptual hash for an image file.
    // Needs error handling for file access, image loading, hashing errors.
    // Uses imagehash library.
    // TDD: Test calculates correct pHash for known image.
    // TDD: Test handles non-image file gracefully (returns None).
    // TDD: Test handles file read errors (returns None or raises).
    pass

FUNCTION check_zip_structure_task(file_path: String): Boolean
    // Worker task: Use zipfile.testzip() to check basic archive integrity.
    // Returns True if corrupt, False otherwise. Handles errors.
    // TDD: Test returns False for valid zip.
    // TDD: Test returns True for corrupt zip.
    // TDD: Test handles non-zip file.
    pass

FUNCTION update_similarity_hashes(db_conn: DBConnection, results: List[Tuple[String, String]]):
    // Batch update FileMetadata.similarity_hash
    // Use UPDATE ... FROM (VALUES ...) syntax if available, or multiple UPDATEs.
    // TDD: Test updates correct records with correct hashes.
    pass

FUNCTION update_similarity_groups(db_conn: DBConnection, updates: List[Tuple[String, String]]):
    // Batch update FileMetadata.similarity_group_id
    // TDD: Test updates correct records with correct group IDs.
    pass

FUNCTION update_analysis_flags(db_conn: DBConnection, flag_updates: List[Tuple[String, String]]):
    // Batch update FileMetadata.analysis_flags using list_append_unique
    // TDD: Test appends flags correctly to existing lists.
    // TDD: Test creates list if flags column was NULL.
    pass

FUNCTION apply_similarity_prioritization(db_conn: DBConnection, file_ids: List[String], config: Dict): List[String]
    // Query metadata for file_ids. Apply prioritization rules from config (resolution, size, date, name patterns, corruption flags).
    // Return list of file_ids considered "best" to keep.
    // TDD: Test prioritization by resolution (higher is better).
    // TDD: Test prioritization by size (larger is better).
    // TDD: Test prioritization by date (newer is better).
    // TDD: Test prioritization by name pattern.
    // TDD: Test prioritization avoids files with corruption flags.
    // TDD: Test combining multiple prioritization rules.
    pass

FUNCTION build_sql_filter(rule: TransferRule, scan_session_id: String): Tuple[String, List]
    // Constructs the WHERE clause and parameters based on rule source and filters.
    // Handles path matching, category matching (using analysis_flags), pattern matching, size/date ranges, flag checks.
    // Needs careful SQL injection prevention (use parameters ?).
    pass

// Other helpers: calculate_optimal_workers, wait_for_completed_futures, generate_short_uuid, 
// calculate_cutoff_date, generate_action_id, create_sql_placeholder_list etc.

// --- Exceptions ---
CLASS AnalysisError(Exception): pass
```
#### TDD Anchors:
- Test pool initialization.
- Test successful DB connection.
- Test duplicate finding called if enabled.
- Test attribute rules application.
- Test similarity finding called if enabled.
- Test corruption checking called if enabled.
- Test disorganization metrics calculation is called if enabled.
- Test transfer rule matching.
- Test handling DB/unexpected errors during analysis run.
- Test DB connection closed on success/failure.
- Test pool shutdown waits for completion.
- Test duplicate query finds hashes/handles none found.
- Test duplicate update query flags correct files/handles list_append_unique.
- Test handling DB error during duplicate finding.
- Test large file rule flags correct files/ignores directories.
- Test old file rule flags correct files based on mtime/atime/ignores directories.
- Test temp file pattern matching rule.
- Test zero-byte file rule.
- Test empty folder rule.
- Test handling DB errors during attribute rules.
- Test query selects correct candidate image files for similarity.
- Test submitting pHash task.
- Test collecting valid pHash result.
- Test handling failed pHash task.
- Test batch update of similarity hashes.
- Test finding exact pHash match groups.
- Test prioritization logic selects correct files based on rules.
- Test non-prioritized files get flagged.
- Test batch update of group IDs/priority flags.
- Test handling DB/unexpected errors during similarity analysis.
- Test query selects zip files for corruption check.
- Test submitting zip check task.
- Test collecting zip corruption result.
- Test handling failed zip check task.
- Test updating basic corruption flags.
- Test header check task.
- Test basic PDF check task.
- Test submitting/collecting full PDF check task.
- Test submitting/collecting ffmpeg check task.
- Test root file ratio calculation.
- Test average folder depth calculation.
- Test flagging based on metric thresholds.
- Test building WHERE clause for path/category/pattern/size/date/flag filters.
- Test combining multiple filters correctly (AND logic).
- Test INSERT statement creates correct ActionItem records.
- Test rule matching ignores files with existing pending/confirmed actions.
- Test handling DB/unexpected errors during rule matching.
- Test pHash worker task calculates hash/handles errors.
- Test zip check worker task returns correct boolean/handles errors.
- Test batch update helpers for similarity/flags.
- Test similarity prioritization logic with various rules.
- Test SQL filter builder handles different rule sources/filters.

### Pseudocode: Scanner Service - Traversing & Hashing
- Created: 2025-04-29 20:26:39
- Updated: 2025-04-29 20:26:39
```pseudocode
// File: pseudocode/scanner.pseudo
// Component: Scanner Service (Pool & Workers)
// --- Constants ---
CONSTANT HASH_CHUNK_SIZE = 4 * 1024 * 1024 // 4MB chunks for hashing
CONSTANT DB_QUEUE_SENTINEL = None // From metadata_store.pseudo

// --- Data Structures ---
// FileMetadataDict (Matches Scanner Output Queue Item - see metadata_store.pseudo)
// ConfigManager (Provides scan paths, credentials - see config_manager.pseudo)
// DBConnection (For read-only incremental checks - needs careful connection management across processes)
// Queue (Multiprocessing queue for results)
// CloudClient (Abstract representation of OneDrive/GDrive SDK client)

// --- Module: ScannerService ---

CLASS ScannerService:
    PRIVATE config_manager: ConfigManager
    PRIVATE db_path: String
    PRIVATE output_queue: Queue
    PRIVATE process_pool: ProcessPoolExecutor // Or multiprocessing.Pool
    PRIVATE scan_session_id: String

    FUNCTION __init__(config_manager: ConfigManager, output_queue: Queue):
        self.config_manager = config_manager
        self.db_path = config_manager.get_db_path()
        self.output_queue = output_queue
        // Determine optimal number of worker processes
        num_workers = calculate_optimal_workers() 
        self.process_pool = ProcessPoolExecutor(max_workers=num_workers)
        // TDD: Test pool initialization with calculated workers.

    FUNCTION start_scan(scan_paths: List[String] = None, full_rescan: Boolean = False):
        // Generates a unique ID for this scan run
        self.scan_session_id = generate_uuid() 
        log_info("Starting scan session: " + self.scan_session_id)

        paths_to_scan = scan_paths IF scan_paths IS NOT None ELSE self.config_manager.get_scan_paths()
        // TDD: Test uses provided paths if given.
        // TDD: Test uses config paths if none provided.

        IF len(paths_to_scan) == 0:
            log_warning("No scan paths configured or provided. Scan aborted.")
            RETURN

        // Submit tasks to the process pool
        futures = []
        FOR path_uri IN paths_to_scan:
            // Pass necessary info to worker: path, session ID, DB path (for reads), queue, config snapshot?, rescan flag
            future = self.process_pool.submit(scan_worker_entrypoint, 
                                               path_uri, 
                                               self.scan_session_id, 
                                               self.db_path, 
                                               self.output_queue, 
                                               full_rescan,
                                               self.config_manager) // Pass config or relevant parts carefully
            futures.append(future)
            // TDD: Test submitting local path task.
            // TDD: Test submitting cloud path task (e.g., "onedrive:/").

        // Wait for all tasks to complete (optional, could monitor progress)
        wait_for_all_futures(futures) 
        log_info("Scan tasks submitted. Workers processing.")
        // TDD: Test waits for futures if required by design.

        // Signal DB writer that scanning is done (might be done elsewhere, e.g., main CLI orchestrator)
        // self.output_queue.put(DB_QUEUE_SENTINEL) 

    FUNCTION shutdown():
        log_info("Shutting down scanner process pool...")
        self.process_pool.shutdown(wait=True)
        log_info("Scanner process pool shut down.")
        // TDD: Test shutdown waits for pool completion.

// --- Worker Process Logic ---

FUNCTION scan_worker_entrypoint(path_uri: String, scan_session_id: String, db_path: String, output_queue: Queue, full_rescan: Boolean, config_manager: ConfigManager):
    // Entry point for each worker process. Sets up DB connection for reads.
    db_conn_read = None
    TRY
        // Each worker needs its own read connection if querying directly
        db_conn_read = duckdb_connect(db_path, read_only=True) 
        log_debug("Worker started for path: " + path_uri)

        IF is_cloud_path(path_uri):
            scan_cloud_location(path_uri, scan_session_id, db_conn_read, output_queue, full_rescan, config_manager)
        ELSE:
            scan_local_directory(path_uri, scan_session_id, db_conn_read, output_queue, full_rescan)
        
        log_debug("Worker finished for path: " + path_uri)

    CATCH Exception as e:
        log_error("Worker failed for path '" + path_uri + "': " + str(e))
        // TDD: Test worker handles exceptions gracefully.
    FINALLY:
        IF db_conn_read IS NOT None:
            db_conn_read.close()

FUNCTION scan_local_directory(dir_path: String, scan_session_id: String, db_conn_read: DBConnection, output_queue: Queue, full_rescan: Boolean):
    // Uses os.scandir for better performance than os.walk
    TRY
        FOR entry IN os_scandir(dir_path):
            TRY
                process_file_entry(entry.path, entry.is_dir(), entry.is_file(), entry.stat(), 
                                   scan_session_id, db_conn_read, output_queue, full_rescan)
                
                IF entry.is_dir():
                    // Recurse into subdirectory
                    scan_local_directory(entry.path, scan_session_id, db_conn_read, output_queue, full_rescan)
                    // TDD: Test recursion into subdirectories.

            CATCH OSError as e: // Permissions error, etc. on stat() or scandir()
                log_warning("Cannot access: " + entry.path + " - " + str(e))
                // TDD: Test skipping inaccessible files/dirs.
    CATCH OSError as e: // Error scanning the top-level dir_path itself
         log_error("Failed to scan directory: " + dir_path + " - " + str(e))
         // TDD: Test handling error scanning top-level directory.

FUNCTION scan_cloud_location(cloud_uri: String, scan_session_id: String, db_conn_read: DBConnection, output_queue: Queue, full_rescan: Boolean, config_manager: ConfigManager):
    // Example for a generic cloud provider
    provider_type, base_path = parse_cloud_uri(cloud_uri) // e.g., "onedrive", "/Documents"
    
    TRY
        client = get_cloud_client(provider_type, config_manager)
        // TDD: Test getting correct cloud client.
        IF client IS None:
            log_error("Could not get cloud client for provider: " + provider_type)
            RETURN

        // Paginate through cloud directory listings
        paginator = client.list_items(base_path) 
        // TDD: Test listing items from cloud root/folder.
        
        FOR page IN paginator:
            FOR item_info IN page: // item_info contains metadata from cloud API
                full_cloud_path = construct_cloud_path(provider_type, item_info.path) // e.g., "onedrive:/Documents/file.txt"
                
                // Adapt process_file_entry to take cloud metadata directly
                process_file_entry(full_cloud_path, item_info.is_directory, item_info.is_file, item_info, // Pass cloud metadata object
                                   scan_session_id, db_conn_read, output_queue, full_rescan, is_cloud=True, cloud_client=client)

                IF item_info.is_directory:
                     // Recurse - construct new URI and call scan_cloud_location
                     scan_cloud_location(full_cloud_path, scan_session_id, db_conn_read, output_queue, full_rescan, config_manager)
                     // TDD: Test recursion into cloud subfolders.
            // TDD: Test handling pagination correctly.

    CATCH CloudAPIError as e:
        log_error("Cloud API error scanning '" + cloud_uri + "': " + str(e))
        // TDD: Test handling cloud API errors during listing.
    CATCH AuthenticationError as e:
        log_error("Cloud authentication error for '" + provider_type + "': " + str(e))
        // TDD: Test handling cloud authentication errors.

FUNCTION process_file_entry(path: String, is_dir: Boolean, is_file: Boolean, entry_info: Any, // os.DirEntry, stat_result, or cloud item object
                           scan_session_id: String, db_conn_read: DBConnection, output_queue: Queue, full_rescan: Boolean, 
                           is_cloud: Boolean = False, cloud_client: CloudClient = None):
    
    current_time = get_current_time()
    existing_record = None
    metadata = FileMetadataDict()
    
    // --- Incremental Check (ADR-004) ---
    IF NOT full_rescan:
        existing_record = query_db_for_path(db_conn_read, path)
        // TDD: Test querying DB for existing path.
        // TDD: Test handling DB query errors.

    // --- Extract Basic Info ---
    metadata['id'] = existing_record['id'] IF existing_record ELSE generate_uuid() // Reuse ID or create new
    metadata['scan_session_id'] = scan_session_id
    metadata['full_path'] = path
    metadata['is_directory'] = is_dir
    metadata['last_seen'] = current_time
    metadata['first_seen'] = existing_record['first_seen'] IF existing_record ELSE current_time
    
    // --- Get Detailed Metadata & Check for Changes ---
    needs_hash = False
    IF is_file:
        current_mtime = None
        current_size = None
        
        TRY:
            IF is_cloud:
                // Cloud metadata already fetched in item_info
                current_mtime = item_info.modified_time 
                current_size = item_info.size_bytes
                // Extract other metadata from item_info
                metadata['created_time'] = item_info.created_time
                metadata['accessed_time'] = None // Often not available/reliable in cloud
                metadata['owner'] = item_info.owner 
                metadata['permissions'] = None // Cloud permissions differ
                metadata['mime_type'] = item_info.mime_type
            ELSE:
                // Local file - entry_info is stat_result
                stat_result = entry_info 
                current_mtime = stat_result.st_mtime
                current_size = stat_result.st_size
                metadata['created_time'] = stat_result.st_ctime
                metadata['accessed_time'] = stat_result.st_atime
                metadata['owner'] = get_file_owner(stat_result.st_uid) // OS specific lookup
                metadata['permissions'] = format_permissions(stat_result.st_mode) // e.g., '0o755'
                metadata['mime_type'] = detect_mime_type(path) // Use python-magic if needed
            
            metadata['size_bytes'] = current_size
            metadata['modified_time'] = current_mtime
            // TDD: Test extracting metadata for local file.
            // TDD: Test extracting metadata for cloud file.

            // Decide if hashing is needed
            IF full_rescan OR existing_record IS None OR \
               existing_record['modified_time'] != current_mtime OR \
               existing_record['size_bytes'] != current_size:
                needs_hash = True
                // TDD: Test needs_hash=True for full rescan.
                // TDD: Test needs_hash=True for new file.
                // TDD: Test needs_hash=True if mtime differs.
                // TDD: Test needs_hash=True if size differs.
            ELSE:
                // Unchanged: Reuse hash from DB
                metadata['sha256_hash'] = existing_record['sha256_hash']
                // Reuse other potentially expensive fields if policy allows
                metadata['mime_type'] = existing_record['mime_type'] 
                // TDD: Test needs_hash=False for unchanged file, reuses hash.

        CATCH Exception as e: // Error getting local stat or parsing cloud info
            log_warning("Metadata error for '" + path + "': " + str(e))
            // Mark as error? Skip? Put minimal info? Decide policy.
            metadata['analysis_flags'] = ['metadata_error'] 
            // TDD: Test handling metadata extraction errors.

    ELSE: // Is Directory
        metadata['size_bytes'] = None
        metadata['sha256_hash'] = None
        // Extract other relevant dir metadata if needed
        // TDD: Test processing a directory sets hash/size to None.

    // --- Calculate Hash if Needed ---
    IF needs_hash AND is_file:
        TRY:
            metadata['sha256_hash'] = calculate_sha256(path, is_cloud, cloud_client)
            // TDD: Test hash calculation for local file.
            // TDD: Test hash calculation for cloud file (requires mocking download).
        CATCH Exception as e:
            log_warning("Hashing error for '" + path + "': " + str(e))
            metadata['sha256_hash'] = None
            metadata['analysis_flags'] = list_append_unique(metadata.get('analysis_flags', []), 'hashing_error')
            // TDD: Test handling hashing errors.

    // --- Finalize and Queue ---
    // Ensure defaults for optional fields if not set
    metadata.setdefault('similarity_hash', None)
    metadata.setdefault('similarity_group_id', None)
    metadata.setdefault('analysis_flags', [])
    metadata.setdefault('disorganization_metric_flags', [])
    metadata.setdefault('ai_suggestion', None)

    output_queue.put(metadata)
    // TDD: Test final metadata dict is put on queue.

FUNCTION calculate_sha256(path: String, is_cloud: Boolean, cloud_client: CloudClient = None): String
    hasher = create_sha256_hasher()
    file_stream = None
    TRY
        IF is_cloud:
            // Stream download from cloud
            file_stream = cloud_client.download_file_stream(path)
            // TDD: Test cloud download stream opened.
        ELSE:
            // Open local file in binary read mode
            file_stream = open_local_file_binary(path)
            // TDD: Test local file stream opened.

        WHILE True:
            chunk = file_stream.read(HASH_CHUNK_SIZE)
            IF NOT chunk:
                BREAK
            hasher.update(chunk)
            // TDD: Test hash updated with chunks.
        
        RETURN hasher.hexdigest()
        // TDD: Test correct hash returned for known content.

    CATCH FileNotFoundError:
        log_warning("File not found during hashing: " + path)
        raise // Re-raise to be caught by process_file_entry
    CATCH PermissionError:
        log_warning("Permission denied during hashing: " + path)
        raise // Re-raise
    CATCH CloudAPIError as e:
        log_warning("Cloud API error during download for hashing '" + path + "': " + str(e))
        raise // Re-raise
    CATCH IOError as e:
        log_warning("I/O error during hashing '" + path + "': " + str(e))
        raise // Re-raise
    FINALLY:
        IF file_stream IS NOT None:
            file_stream.close()
            // TDD: Test file stream is closed on success.
            // TDD: Test file stream is closed on error.

FUNCTION query_db_for_path(db_conn_read: DBConnection, path: String): Dict OR None
    // Executes a SELECT query on FileMetadata table for the given path.
    // Returns dictionary representation of the row or None if not found.
    TRY:
        result = db_conn_read.execute("SELECT * FROM FileMetadata WHERE full_path = ?", [path]).fetchone()
        RETURN result_row_to_dict(result) IF result ELSE None
    CATCH DuckDBError as e:
        log_error("DB query failed for path '" + path + "': " + str(e))
        RETURN None // Or raise? If DB read fails, incremental scan is compromised.

// --- Helper Functions ---
FUNCTION get_cloud_client(provider_type: String, config_manager: ConfigManager): CloudClient OR None
    // Uses config_manager to get credentials and initialize the appropriate SDK client.
    // Handles authentication flow. Returns client instance or None on failure.
    // Needs implementation per cloud provider (OneDrive, GDrive).
    // Uses tenacity for retries during authentication/initialization if needed.
    // TDD: Test getting OneDrive client with mock credentials.
    // TDD: Test getting GDrive client with mock credentials.
    // TDD: Test returns None if credentials missing/invalid.
    pass 

FUNCTION is_cloud_path(path_uri: String): Boolean
    // Checks if path starts with a known cloud prefix like "onedrive:", "gdrive:"
    pass

FUNCTION parse_cloud_uri(path_uri: String): Tuple[String, String]
    // Splits "onedrive:/Documents/file.txt" into ("onedrive", "/Documents/file.txt")
    pass

FUNCTION construct_cloud_path(provider: String, item_path: String): String
    // Combines "onedrive" and "/Documents/file.txt" into "onedrive:/Documents/file.txt"
    pass

// Other helpers: generate_uuid, calculate_optimal_workers, wait_for_all_futures, 
// result_row_to_dict, get_file_owner, format_permissions, detect_mime_type, 
// list_append_unique, open_local_file_binary, create_sha256_hasher etc.

// --- Exceptions ---
CLASS ScanError(Exception): pass
CLASS CloudAPIError(Exception): pass
CLASS AuthenticationError(Exception): pass
```
#### TDD Anchors:
- Test pool initialization with calculated workers.
- Test start_scan uses provided paths/config paths.
- Test submitting local/cloud path task.
- Test start_scan waits for futures if required.
- Test shutdown waits for pool completion.
- Test worker handles exceptions gracefully.
- Test recursion into local subdirectories.
- Test skipping inaccessible local files/dirs.
- Test handling error scanning top-level local directory.
- Test getting correct cloud client.
- Test listing items from cloud root/folder.
- Test recursion into cloud subfolders.
- Test handling cloud pagination correctly.
- Test handling cloud API/authentication errors during listing.
- Test querying DB for existing path/handles DB errors.
- Test extracting metadata for local file.
- Test extracting metadata for cloud file.
- Test needs_hash=True for full rescan/new file/mtime diff/size diff.
- Test needs_hash=False for unchanged file, reuses hash.
- Test handling metadata extraction errors.
- Test processing a directory sets hash/size to None.
- Test hash calculation for local file.
- Test hash calculation for cloud file (mock download).
- Test handling hashing errors (FileNotFound, Permission, CloudAPI, IO).
- Test final metadata dict is put on queue.
- Test cloud download stream opened.
- Test local file stream opened.
- Test hash updated with chunks.
- Test correct hash returned for known content.
- Test file stream closed on success/error.
- Test getting OneDrive/GDrive client with mock credentials.
- Test get_cloud_client returns None if credentials missing/invalid.

### Pseudocode: Metadata Store - DB Interaction & Writer
- Created: 2025-04-29 20:25:41
- Updated: 2025-04-29 20:25:41
```pseudocode
// File: pseudocode/metadata_store.pseudo
// Component: Metadata Store (DuckDB Interaction & DB Writer Process)
// --- Constants ---
CONSTANT DB_WRITE_BATCH_SIZE = 1000
CONSTANT DB_WRITE_TIMEOUT_SECONDS = 5
CONSTANT DB_QUEUE_SENTINEL = None // Signal to stop the writer process

// --- Data Structures ---
// FileMetadataDict (Matches Scanner Output Queue Item)
//   - id: String (UUID or generated hash?)
//   - scan_session_id: String
//   - full_path: String
//   - is_directory: Boolean
//   - size_bytes: Integer
//   - created_time: Timestamp
//   - modified_time: Timestamp
//   - accessed_time: Timestamp
//   - owner: String
//   - permissions: String
//   - mime_type: String
//   - sha256_hash: String
//   - similarity_hash: String (Optional)
//   - similarity_group_id: String (Optional)
//   - analysis_flags: List[String] (Initially empty)
//   - disorganization_metric_flags: List[String] (Initially empty)
//   - ai_suggestion: String (Optional)
//   - last_seen: Timestamp
//   - first_seen: Timestamp

// --- Module: MetadataStore ---

// This module primarily defines the schema and the DB Writer process.
// Direct DB connections for reading/analysis are handled by other components.

FUNCTION initialize_database(db_path: String):
    // Connects to DuckDB and ensures tables exist.
    db_conn = duckdb_connect(db_path, read_only=False)
    // TDD: Test connection successful with valid path.
    // TDD: Test connection fails with invalid path.
    TRY
        // Create FileMetadata Table (Idempotent)
        db_conn.execute("""
            CREATE TABLE IF NOT EXISTS FileMetadata (
              id VARCHAR PRIMARY KEY, -- Using VARCHAR for potential UUID/hash ID
              scan_session_id VARCHAR,
              full_path VARCHAR UNIQUE NOT NULL,
              is_directory BOOLEAN NOT NULL,
              size_bytes BIGINT,
              created_time TIMESTAMP,
              modified_time TIMESTAMP,
              accessed_time TIMESTAMP,
              owner VARCHAR,
              permissions VARCHAR,
              mime_type VARCHAR,
              sha256_hash VARCHAR,
              similarity_hash VARCHAR,
              similarity_group_id VARCHAR,
              analysis_flags LIST(VARCHAR),
              disorganization_metric_flags LIST(VARCHAR),
              ai_suggestion VARCHAR,
              last_seen TIMESTAMP NOT NULL,
              first_seen TIMESTAMP NOT NULL
            );
        """)
        // TDD: Test table creation if not exists.
        // TDD: Test command runs without error if table already exists.

        // Create ActionItem Table (Idempotent)
        db_conn.execute("""
            CREATE TABLE IF NOT EXISTS ActionItem (
              id BIGINT PRIMARY KEY, -- Consider AUTOINCREMENT or sequence
              file_id VARCHAR NOT NULL REFERENCES FileMetadata(id) ON DELETE CASCADE,
              rule_name VARCHAR,
              action_type VARCHAR NOT NULL,
              target_path VARCHAR,
              status VARCHAR NOT NULL,
              result_message VARCHAR,
              suggestion_time TIMESTAMP NOT NULL,
              confirmation_time TIMESTAMP,
              execution_time TIMESTAMP
            );
        """)
        // TDD: Test table creation if not exists.
        // TDD: Test command runs without error if table already exists.

        // Create Indexes (Idempotent) - Add more as needed based on query patterns
        db_conn.execute("CREATE INDEX IF NOT EXISTS idx_fm_fullpath ON FileMetadata(full_path);")
        db_conn.execute("CREATE INDEX IF NOT EXISTS idx_fm_hash ON FileMetadata(sha256_hash);")
        db_conn.execute("CREATE INDEX IF NOT EXISTS idx_fm_mtime ON FileMetadata(modified_time);")
        db_conn.execute("CREATE INDEX IF NOT EXISTS idx_fm_size ON FileMetadata(size_bytes);")
        db_conn.execute("CREATE INDEX IF NOT EXISTS idx_fm_lastseen ON FileMetadata(last_seen);")
        db_conn.execute("CREATE INDEX IF NOT EXISTS idx_ai_status ON ActionItem(status);")
        db_conn.execute("CREATE INDEX IF NOT EXISTS idx_ai_fileid ON ActionItem(file_id);")
        // TDD: Test index creation.

        log_info("Database schema initialized successfully at: " + db_path)

    CATCH DuckDBError as e:
        log_error("Failed to initialize database schema: " + str(e))
        raise DatabaseInitializationError("Could not create/verify database tables.")
    FINALLY:
        db_conn.close()
    // TDD: Test handling of DuckDBError during initialization.

// --- Module: DBWriterProcess ---

FUNCTION db_writer_process_loop(db_path: String, input_queue: Queue):
    // This function runs in a separate process.
    db_conn = None
    batch = []
    last_write_time = get_current_time()

    TRY
        db_conn = duckdb_connect(db_path, read_only=False)
        // TDD: Test writer process connects to DB successfully.
        log_info("DB Writer process started. Connected to: " + db_path)

        WHILE True:
            item = None
            TRY:
                // Wait for an item or timeout
                item = input_queue.get(timeout=DB_WRITE_TIMEOUT_SECONDS)
                // TDD: Test receiving item from queue.
            CATCH QueueEmpty:
                // Timeout occurred, check if we need to write the current batch
                pass
            // TDD: Test handling queue timeout.

            IF item IS DB_QUEUE_SENTINEL:
                log_info("DB Writer received sentinel. Writing final batch...")
                write_batch_to_db(db_conn, batch)
                batch = []
                BREAK // Exit the loop
            ELSE IF item IS NOT None:
                batch.append(item)

            // Write batch if size reached or timeout occurred and batch has items
            current_time = get_current_time()
            IF len(batch) >= DB_WRITE_BATCH_SIZE OR \
               (len(batch) > 0 AND (current_time - last_write_time) > DB_WRITE_TIMEOUT_SECONDS):
                write_batch_to_db(db_conn, batch)
                batch = [] // Clear the batch
                last_write_time = current_time
                // TDD: Test batch write triggered by size.
                // TDD: Test batch write triggered by timeout.

    CATCH DuckDBError as e:
        log_error("DB Writer process encountered a database error: " + str(e))
        // Handle error - log failed batch items? Terminate?
    CATCH Exception as e:
        log_error("DB Writer process encountered an unexpected error: " + str(e))
    FINALLY:
        IF db_conn IS NOT None:
            db_conn.close()
        log_info("DB Writer process finished.")
    // TDD: Test graceful shutdown on sentinel.
    // TDD: Test handling DuckDBError during loop.
    // TDD: Test handling unexpected Exception during loop.

FUNCTION write_batch_to_db(db_conn: DuckDBConnection, batch: List[FileMetadataDict]):
    IF len(batch) == 0:
        RETURN

    log_debug("Writing batch of " + str(len(batch)) + " items to DB.")
    TRY
        // Prepare data for insertion (e.g., list of tuples matching table order)
        // Ensure correct handling of LIST types if using parameter substitution
        prepared_data = prepare_data_for_upsert(batch)

        // Use INSERT ... ON CONFLICT for efficient upserts
        // Note: DuckDB syntax might vary slightly, check documentation.
        // Assumes 'id' or 'full_path' is the conflict target. Using 'full_path'.
        sql = """
            INSERT INTO FileMetadata (
                id, scan_session_id, full_path, is_directory, size_bytes,
                created_time, modified_time, accessed_time, owner, permissions,
                mime_type, sha256_hash, similarity_hash, similarity_group_id,
                analysis_flags, disorganization_metric_flags, ai_suggestion,
                last_seen, first_seen
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) -- Placeholder count matches columns
            ON CONFLICT (full_path) DO UPDATE SET
                scan_session_id = excluded.scan_session_id,
                is_directory = excluded.is_directory,
                size_bytes = excluded.size_bytes,
                created_time = excluded.created_time,
                modified_time = excluded.modified_time,
                accessed_time = excluded.accessed_time,
                owner = excluded.owner,
                permissions = excluded.permissions,
                mime_type = excluded.mime_type,
                sha256_hash = excluded.sha256_hash,
                -- Only update similarity if new value provided? Or always overwrite? Decide policy.
                similarity_hash = excluded.similarity_hash,
                similarity_group_id = excluded.similarity_group_id,
                -- How to handle list updates? Overwrite or merge? Overwrite is simpler.
                analysis_flags = excluded.analysis_flags,
                disorganization_metric_flags = excluded.disorganization_metric_flags,
                ai_suggestion = excluded.ai_suggestion,
                last_seen = excluded.last_seen
                -- Do NOT update first_seen on conflict
        """
        // db_conn.executemany(sql, prepared_data) // Use executemany if supported and efficient
        // OR construct a single large INSERT with multiple VALUES clauses if more performant
        db_conn.execute(sql, parameters=prepared_data) // Adjust based on actual DuckDB API for batch inserts

        db_conn.commit() // Commit the transaction
        log_debug("Batch write successful.")
        // TDD: Test writing a batch inserts new records correctly.
        // TDD: Test writing a batch updates existing records correctly based on full_path.
        // TDD: Test 'first_seen' is NOT updated on conflict.
        // TDD: Test 'last_seen' IS updated on conflict.
    CATCH DuckDBError as e:
        log_error("Failed to write batch to database: " + str(e))
        db_conn.rollback() // Rollback on error
        // Consider logging failed items from the batch
        raise // Re-raise the exception to be caught by the main loop
    // TDD: Test handling DuckDBError during write rolls back transaction.

FUNCTION prepare_data_for_upsert(batch: List[FileMetadataDict]): List[Tuple]
    // Convert list of dictionaries to list of tuples in the correct column order
    // Handle potential None values and data type conversions if necessary
    // Generate unique ID (e.g., UUID) if not provided by scanner
    prepared = []
    FOR item IN batch:
        IF item.get('id') IS None:
            item['id'] = generate_uuid() // Or use hash-based ID

        // Ensure all fields exist, defaulting to None if missing from dict
        tuple_data = (
            item.get('id'),
            item.get('scan_session_id'),
            item.get('full_path'),
            item.get('is_directory'),
            item.get('size_bytes'),
            item.get('created_time'),
            item.get('modified_time'),
            item.get('accessed_time'),
            item.get('owner'),
            item.get('permissions'),
            item.get('mime_type'),
            item.get('sha256_hash'),
            item.get('similarity_hash'),
            item.get('similarity_group_id'),
            item.get('analysis_flags', []), // Default to empty list
            item.get('disorganization_metric_flags', []), // Default to empty list
            item.get('ai_suggestion'),
            item.get('last_seen'),
            item.get('first_seen')
        )
        prepared.append(tuple_data)
    RETURN prepared
    // TDD: Test conversion handles missing optional fields correctly.
    // TDD: Test conversion generates ID if missing.
    // TDD: Test conversion handles list types correctly.

// --- Exceptions ---
CLASS DatabaseInitializationError(Exception): pass
CLASS DatabaseWriteError(Exception): pass // May not be needed if DuckDBError is handled
```
#### TDD Anchors:
- Test DB connection successful/fails with invalid path.
- Test table creation if not exists/runs without error if exists (FileMetadata, ActionItem).
- Test index creation.
- Test handling DuckDBError during initialization.
- Test writer process connects to DB successfully.
- Test receiving item from queue.
- Test handling queue timeout.
- Test batch write triggered by size.
- Test batch write triggered by timeout.
- Test graceful shutdown on sentinel.
- Test handling DuckDBError/Exception during writer loop.
- Test writing batch inserts new records correctly.
- Test writing batch updates existing records correctly based on full_path.
- Test 'first_seen' is NOT updated on conflict.
- Test 'last_seen' IS updated on conflict.
- Test handling DuckDBError during write rolls back transaction.
- Test data preparation handles missing optional fields/generates ID/handles list types.

### Pseudocode: Configuration Manager - Loading & Credentials
- Created: 2025-04-29 20:25:01
- Updated: 2025-04-29 20:25:01
```pseudocode
// File: pseudocode/config_manager.pseudo
// Component: Configuration Manager
// --- Constants ---
CONSTANT DEFAULT_CONFIG_DIR = get_user_config_dir("storage-hygeine")
CONSTANT DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.yaml"
CONSTANT DEFAULT_DB_DIR = get_user_data_dir("storage-hygeine")
CONSTANT DEFAULT_DB_FILE = DEFAULT_DB_DIR / "metadata.duckdb"
CONSTANT KEYRING_SERVICE_NAME = "storage-hygeine"

// --- Data Structures ---
// ConfigSchema (Validated structure, e.g., using Pydantic)
//   - scan_paths: List[String]
//   - analysis_rules: Dict[String, RuleConfig]
//   - transfer_rules: List[TransferRule]
//   - log_level: String
//   - db_path: String
//   - ... other settings

// RuleConfig (Example for 'large_files')
//   - enabled: Boolean
//   - threshold_mb: Integer

// TransferRule (Based on ADR-007)
//   - name: String
//   - action_type: String ('COPY', 'MOVE')
//   - source: String (path, cloud path, or 'category:...')
//   - destination: String (path, cloud path, 'TRASH', 'PERMANENT_DELETE')
//   - filters: Optional[Dict] (patterns, size, date, flags)
//   - options: Optional[Dict] (conflict_resolution, delete_source_after_transfer)

// --- Module: ConfigManager ---

CLASS ConfigManager:
    PRIVATE config_data: ConfigSchema
    PRIVATE config_file_path: Path

    // --- Initialization ---
    FUNCTION __init__(config_path=DEFAULT_CONFIG_FILE):
        self.config_file_path = Path(config_path)
        self.config_data = self.load_config()
        // TDD: Test initialization with default path.
        // TDD: Test initialization with custom path.
        // TDD: Test initialization creates default config if file not found.

    // --- Core Methods ---
    FUNCTION load_config(): ConfigSchema
        TRY
            IF NOT self.config_file_path.exists():
                create_default_config(self.config_file_path)
                // TDD: Test that default config is created correctly.
            
            yaml_content = read_file_content(self.config_file_path)
            raw_config = parse_yaml(yaml_content)
            
            // Validate raw_config against ConfigSchema (e.g., using Pydantic)
            validated_config = validate_schema(raw_config, ConfigSchema)
            // TDD: Test validation success with valid config.
            // TDD: Test validation failure with invalid config (missing keys, wrong types).
            
            // Ensure essential defaults if missing after validation (e.g., db_path)
            IF validated_config.db_path IS NULL OR EMPTY:
                 validated_config.db_path = DEFAULT_DB_FILE
            ensure_directory_exists(Path(validated_config.db_path).parent)

            RETURN validated_config
        CATCH FileNotFoundError:
            log_error("Config file not found at: " + self.config_file_path)
            // Potentially re-create default or raise critical error
            raise ConfigurationError("Config file missing and could not be created.")
        CATCH YamlParseError:
            log_error("Error parsing YAML config file: " + self.config_file_path)
            raise ConfigurationError("Invalid YAML format in config file.")
        CATCH ValidationError as e:
            log_error("Config validation failed: " + str(e))
            raise ConfigurationError("Invalid configuration structure or values.")
        // TDD: Test handling of FileNotFoundError during load.
        // TDD: Test handling of YamlParseError during load.
        // TDD: Test handling of ValidationError during load.

    FUNCTION save_config():
        // Only save non-sensitive parts back to YAML
        config_to_save = filter_sensitive_data(self.config_data) 
        yaml_string = format_as_yaml(config_to_save)
        TRY
            ensure_directory_exists(self.config_file_path.parent)
            write_to_file(self.config_file_path, yaml_string)
            // TDD: Test saving valid config writes correct YAML.
        CATCH IOError as e:
            log_error("Failed to save config file: " + str(e))
            raise ConfigurationError("Could not write config file.")
        // TDD: Test handling of IOError during save.

    FUNCTION get_setting(key_path: String, default=None): Any
        // Access nested settings using dot notation, e.g., "analysis_rules.large_files.threshold_mb"
        value = access_nested_dict(self.config_data, key_path)
        RETURN value IF value IS NOT None ELSE default
        // TDD: Test getting existing top-level setting.
        // TDD: Test getting existing nested setting.
        // TDD: Test getting non-existent setting returns default.

    FUNCTION set_setting(key_path: String, value: Any):
        // Set nested settings using dot notation
        // Validate value type if possible before setting
        set_nested_dict(self.config_data, key_path, value)
        // TDD: Test setting top-level setting updates internal data.
        // TDD: Test setting nested setting updates internal data.
        // TDD: Test setting invalid value type raises error (if validation added).
        // Consider triggering save_config() or requiring explicit save call

    FUNCTION get_scan_paths(): List[String]
        RETURN self.config_data.scan_paths OR []
        // TDD: Test returns correct paths from config.
        // TDD: Test returns empty list if not defined.

    FUNCTION get_analysis_rules(): Dict[String, RuleConfig]
        RETURN self.config_data.analysis_rules OR {}
        // TDD: Test returns correct rules dict.

    FUNCTION get_transfer_rules(): List[TransferRule]
        RETURN self.config_data.transfer_rules OR []
        // TDD: Test returns correct transfer rules list.

    FUNCTION get_db_path(): String
        RETURN self.config_data.db_path // Default set during load
        // TDD: Test returns correct DB path.

    // --- Credential Management (using OS Keychain via 'keyring') ---
    FUNCTION get_credential(service_key: String): String OR None
        // service_key examples: "onedrive_client_secret", "gdrive_api_key", "vertex_ai_key"
        TRY
            // Use KEYRING_SERVICE_NAME to scope credentials
            password = keyring_get_password(KEYRING_SERVICE_NAME, service_key)
            RETURN password
            // TDD: Test getting existing credential returns correct value (requires mocking keyring).
        CATCH KeyringError as e:
            log_warning("Could not retrieve credential '" + service_key + "' from keyring: " + str(e))
            RETURN None
        // TDD: Test getting non-existent credential returns None (requires mocking keyring).
        // TDD: Test handling keyring backend errors returns None (requires mocking keyring).

    FUNCTION set_credential(service_key: String, credential_value: String): Boolean
        TRY
            keyring_set_password(KEYRING_SERVICE_NAME, service_key, credential_value)
            log_info("Credential '" + service_key + "' stored successfully.")
            RETURN True
            // TDD: Test setting credential stores value (requires mocking keyring).
        CATCH KeyringError as e:
            log_error("Failed to store credential '" + service_key + "' in keyring: " + str(e))
            RETURN False
        // TDD: Test handling keyring backend errors returns False (requires mocking keyring).

    FUNCTION delete_credential(service_key: String): Boolean
        TRY
            keyring_delete_password(KEYRING_SERVICE_NAME, service_key)
            log_info("Credential '" + service_key + "' deleted successfully.")
            RETURN True
            // TDD: Test deleting existing credential works (requires mocking keyring).
        CATCH PasswordDeleteError:
             log_info("Credential '" + service_key + "' not found to delete.")
             RETURN True // Or False depending on desired semantics
        CATCH KeyringError as e:
            log_error("Failed to delete credential '" + service_key + "' from keyring: " + str(e))
            RETURN False
        // TDD: Test deleting non-existent credential (requires mocking keyring).
        // TDD: Test handling keyring backend errors returns False (requires mocking keyring).

    FUNCTION ensure_credential(service_key: String, prompt_message: String): String OR None
        // Tries to get credential, prompts user via CLI if missing, sets it, then returns it.
        credential = self.get_credential(service_key)
        IF credential IS None:
            log_info("Credential '" + service_key + "' not found in keyring.")
            // This function needs access to a CLI interaction module/function
            user_input = prompt_user_for_secret(prompt_message) 
            IF user_input IS NOT None AND user_input IS NOT EMPTY:
                IF self.set_credential(service_key, user_input):
                    RETURN user_input
                ELSE:
                    log_error("Failed to store the provided credential.")
                    RETURN None
            ELSE:
                log_warning("No credential provided by user.")
                RETURN None
        ELSE:
            RETURN credential
        // TDD: Test returns existing credential without prompting.
        // TDD: Test prompts user if credential missing (mock CLI & keyring).
        // TDD: Test successfully sets and returns credential after prompt.
        // TDD: Test returns None if user provides no input.
        // TDD: Test returns None if setting credential fails after prompt.

// --- Helper Functions ---
FUNCTION create_default_config(file_path: Path):
    default_config = {
        "scan_paths": [],
        "analysis_rules": {
            "duplicates": {"enabled": True},
            "large_files": {"enabled": True, "threshold_mb": 1024},
            "old_files": {"enabled": True, "days_threshold": 365},
            // Add other default rules...
        },
        "transfer_rules": [],
        "log_level": "INFO",
        "db_path": str(DEFAULT_DB_FILE) 
    }
    yaml_string = format_as_yaml(default_config)
    ensure_directory_exists(file_path.parent)
    write_to_file(file_path, yaml_string)
    log_info("Created default config file at: " + str(file_path))

FUNCTION ensure_directory_exists(dir_path: Path):
    IF NOT dir_path.exists():
        create_directories(dir_path)

// --- Exceptions ---
CLASS ConfigurationError(Exception): pass
```
#### TDD Anchors:
- Test initialization with default/custom path.
- Test initialization creates default config if file not found.
- Test default config created correctly.
- Test validation success with valid config.
- Test validation failure with invalid config.
- Test handling FileNotFoundError/YamlParseError/ValidationError during load.
- Test saving valid config writes correct YAML.
- Test handling IOError during save.
- Test getting existing top-level/nested setting.
- Test getting non-existent setting returns default.
- Test setting top-level/nested setting updates internal data.
- Test setting invalid value type raises error.
- Test get_scan_paths returns correct paths/empty list.
- Test get_analysis_rules returns correct dict.
- Test get_transfer_rules returns correct list.
- Test get_db_path returns correct path.
- Test getting existing credential returns correct value (mock keyring).
- Test getting non-existent credential returns None (mock keyring).
- Test handling keyring backend errors returns None (mock keyring).
- Test setting credential stores value (mock keyring).
- Test handling keyring backend errors returns False (mock keyring).
- Test deleting existing/non-existent credential (mock keyring).
- Test handling keyring backend errors returns False (mock keyring).
- Test ensure_credential returns existing credential without prompting.
- Test ensure_credential prompts user if missing (mock CLI & keyring).
- Test ensure_credential sets and returns credential after prompt.
- Test ensure_credential returns None if user provides no input/setting fails.

## Edge Cases
<!-- Append new edge cases using the format below -->

## System Constraints
<!-- Append new constraints using the format below -->

## Functional Requirements
<!-- Append new requirements using the format below -->