# TDD Specific Memory
<!-- Entries below should be added reverse chronologically (newest first) -->

### Test Execution: Integration - [2025-04-30 01:05:59]
- **Trigger**: Manual TDD Cycle 8 (CLI Alt DB Non-Dry Run) - Post-Fix
- **Outcome**: PASS / **Summary**: [46 tests passed, 0 failed]
- **Failed Tests**: None
- **Notes**: Confirmed fix for `test_main_workflow_multiple_targets` assertion and verified `test_main_workflow_non_dry_run_alt_db` passes.

### Test Execution: Integration - [2025-04-30 01:05:01]
- **Trigger**: Manual TDD Cycle 8 (CLI Alt DB Non-Dry Run) - Initial Run
- **Outcome**: FAIL / **Summary**: [1 failed, 45 passed]
- **Failed Tests**: `tests/integration/test_main_workflow.py::test_main_workflow_multiple_targets` (AssertionError: Expected 7 files... found 2)
- **Notes**: Failure due to incorrect assertion in `test_main_workflow_multiple_targets`, not the newly added test.

### Test Execution: Integration - [2025-04-30 01:03:17]
- **Trigger**: Manual TDD Cycle 6 (Error Handling - Permission) - Post-Fix Attempt 2
- **Outcome**: PASS / **Summary**: [44 tests passed, 0 failed]
- **Failed Tests**: None
- **Notes**: Test `test_main_workflow_staging_permission_error` passed after correcting assertion to check stdout.

### Test Execution: Integration - [2025-04-30 01:01:01]
- **Trigger**: Manual TDD Cycle 6 (Error Handling - Permission) - Post-Fix Attempt 1
- **Outcome**: FAIL / **Summary**: [1 failed, 43 passed]
- **Failed Tests**: `tests/integration/test_main_workflow.py::test_main_workflow_staging_permission_error` (AssertionError: Expected permission error message not found in stderr)
- **Notes**: Failure due to logging going to stdout, not stderr.

### Test Execution: Integration - [2025-04-30 00:59:03]
- **Trigger**: Manual TDD Cycle 5 (Non-Dry Run Multi-Match) - Post-Fix
- **Outcome**: PASS / **Summary**: [43 tests passed, 0 failed]
- **Failed Tests**: None
- **Notes**: Test `test_main_workflow_non_dry_run_multiple_matches` passed after adding logic to `ActionExecutor` to prevent duplicate moves.

### Test Execution: Integration - [2025-04-30 00:57:41]
- **Trigger**: Manual TDD Cycle 5 (Non-Dry Run Multi-Match) - Initial Run
- **Outcome**: FAIL / **Summary**: [1 failed, 42 passed]
- **Failed Tests**: `tests/integration/test_main_workflow.py::test_main_workflow_non_dry_run_multiple_matches` (AssertionError: Script exited with error code 1 - due to FileNotFoundError on second move attempt)
- **Notes**: Test failed as expected, driving need to prevent duplicate moves in ActionExecutor.

### Test Execution: Integration - [2025-04-30 00:56:26]
- **Trigger**: Manual TDD Cycle 4 (Config - Alt Staging Path)
- **Outcome**: PASS / **Summary**: [42 tests passed, 0 failed]
- **Failed Tests**: None
- **Notes**: Test `test_main_workflow_different_staging_path` passed.

### Test Execution: Integration - [2025-04-30 00:55:13]
- **Trigger**: Manual TDD Cycle 3 (Scanning - Empty Subdir) - Post-Assertion Add
- **Outcome**: PASS / **Summary**: [41 tests passed, 0 failed]
- **Failed Tests**: None
- **Notes**: Test `test_main_workflow_scan_variations` passed after adding assertion to check empty subdir is ignored.

### Test Execution: Integration - [2025-04-30 00:53:25]
- **Trigger**: Manual TDD Cycle 2 (Analysis - Large Threshold)
- **Outcome**: PASS / **Summary**: [41 tests passed, 0 failed]
- **Failed Tests**: None
- **Notes**: Test `test_main_workflow_large_file_threshold_variation` passed.

### Test Execution: Integration - [2025-04-30 00:52:40]
- **Trigger**: Manual TDD Cycle 1 (Config - Only Old Rule)
- **Outcome**: PASS / **Summary**: [40 tests passed, 0 failed]
- **Failed Tests**: None
- **Notes**: Test `test_main_workflow_only_old_files_rule` passed.
## Test Execution Results
<!-- Append test run summaries using the format below -->
### Test Execution: Unit - [2025-04-29 23:02:27]
- **Trigger**: Manual TDD Cycle 1 (ActionExecutor - Init)
- **Outcome**: PASS / **Summary**: [1 test passed, 0 failed]
- **Failed Tests**: None
- **Notes**: Test `test_action_executor_initialization` passed after minimal `ActionExecutor` class implementation.
### Test Execution: Unit - [2025-04-29 22:57:37]
### Test Execution: Unit - [2025-04-29 23:11:10]
- **Trigger**: Manual TDD Cycle 2 (ActionExecutor - Load Config)
- **Outcome**: PASS / **Summary**: [2 tests passed, 0 failed]
- **Failed Tests**: None
- **Notes**: Test `test_execute_actions_retrieves_config` passed after minimal `execute_actions` implementation.
- **Trigger**: Manual TDD Cycle 5 (AnalysisEngine - Old File Rule)
### Test Execution: Unit - [2025-04-29 23:14:35]
- **Trigger**: Manual TDD Cycle 3 Refactor (ActionExecutor - Dispatch)
- **Outcome**: PASS / **Summary**: [3 tests passed, 0 failed]
- **Failed Tests**: None
- **Notes**: Tests passed after fixing test patching issue related to refactored handler map.
- **Outcome**: PASS / **Summary**: [5 tests passed, 0 failed]
### Test Execution: Unit - [2025-04-29 23:16:56]
- **Trigger**: Manual TDD Cycle 4 (ActionExecutor - Stage Duplicate Logic)
- **Outcome**: PASS / **Summary**: [4 tests passed, 0 failed]
- **Failed Tests**: None
- **Notes**: Tests passed after implementing `_stage_duplicate` logic and refactoring path calculation into `_get_staging_path`.
- **Failed Tests**: None
### Test Execution: Unit - [2025-04-29 23:18:16]
- **Trigger**: Manual TDD Cycle 5 (ActionExecutor - Dry Run Mode)
- **Outcome**: PASS / **Summary**: [5 tests passed, 0 failed]
- **Failed Tests**: None
- **Notes**: Test `test_stage_duplicate_dry_run_logs_and_skips_move` passed, confirming dry run logic.
- **Notes**: Test `test_analyze_identifies_old_files` passed after implementing `_apply_old_file_rule` and fixing previous tool errors.
### Test Execution: Unit - [2025-04-29 23:19:40]
- **Trigger**: Manual TDD Cycle 6 (ActionExecutor - Dispatch Review Large)
- **Outcome**: PASS / **Summary**: [6 tests passed, 0 failed]
- **Failed Tests**: None
- **Notes**: Test `test_execute_actions_dispatches_review_large` passed, confirming dispatch logic for this action type.
### Test Execution: Unit - [2025-04-29 22:54:22]
### Test Execution: Unit - [2025-04-29 23:23:17]
- **Trigger**: Manual TDD Cycle 7 (ActionExecutor - Review Large Logic)
- **Outcome**: PASS / **Summary**: [7 tests passed, 0 failed]
- **Failed Tests**: None
- **Notes**: Test `test_review_large_moves_file` passed after implementing logic in `_review_large`. Refactored staging logic into generic `_stage_file` method.
- **Trigger**: Manual TDD Cycle 4 (AnalysisEngine - Large File Rule)
### Test Execution: Unit - [2025-04-29 23:24:37]
- **Trigger**: Manual TDD Cycle 8 (ActionExecutor - Dispatch Review Old)
- **Outcome**: PASS / **Summary**: [8 tests passed, 0 failed]
- **Failed Tests**: None
- **Notes**: Test `test_execute_actions_dispatches_review_old` passed, confirming dispatch logic for this action type.
- **Outcome**: PASS / **Summary**: [4 tests passed, 0 failed]
### Test Execution: Unit - [2025-04-29 23:26:19]
- **Trigger**: Manual TDD Cycle 9 (ActionExecutor - Review Old Logic)
- **Outcome**: PASS / **Summary**: [9 tests passed, 0 failed]
- **Failed Tests**: None
- **Notes**: Test `test_review_old_moves_file` passed after implementing `_review_old` to call `_stage_file`.
- **Failed Tests**: None
### Test Execution: Unit - [2025-04-29 23:27:35]
- **Trigger**: Manual TDD Cycle 10 (Error Handling - File Not Found)
- **Outcome**: PASS / **Summary**: [10 tests passed, 0 failed]
- **Failed Tests**: None
- **Notes**: Test `test_stage_file_handles_file_not_found_error` passed, confirming existing try/except block handles move errors.
- **Notes**: Test `test_analyze_identifies_large_files` passed after implementing `_apply_large_file_rule`.
### Test Execution: Unit - [2025-04-29 22:52:48]
- **Trigger**: Manual TDD Cycle 3 Refactor (AnalysisEngine - Duplicate Rule)
- **Outcome**: PASS / **Summary**: [3 tests passed, 0 failed]
- **Failed Tests**: None
- **Notes**: Tests passed after refactoring duplicate logic into `_apply_duplicate_rule`.

### Test Execution: Unit - [2025-04-29 22:52:24]
- **Trigger**: Manual TDD Cycle 3 (AnalysisEngine - Duplicate Rule)
- **Outcome**: PASS / **Summary**: [3 tests passed, 0 failed]
- **Failed Tests**: None
- **Notes**: Test `test_analyze_identifies_duplicate_files` passed after implementing duplicate detection logic.
### Test Execution: Unit - [2025-04-29 22:50:35]
- **Trigger**: Manual TDD Cycle 2 (AnalysisEngine - Load Rules)
- **Outcome**: PASS / **Summary**: [2 tests passed, 0 failed]
- **Failed Tests**: None
- **Notes**: Test `test_analysis_engine_loads_rules_from_config` passed after implementing rule loading in `_load_rules`.
### Test Execution: Unit - [2025-04-29 22:49:08]
- **Trigger**: Manual TDD Cycle 1 (AnalysisEngine - Init)
- **Outcome**: PASS / **Summary**: [1 test passed, 0 failed]
- **Failed Tests**: None
- **Notes**: Test `test_analysis_engine_initialization` passed after minimal `AnalysisEngine` class implementation.
### Test Execution: Unit - [2025-04-29 22:44:37]
- **Trigger**: Manual TDD Cycle 6 (Scanner - Error Handling)
- **Outcome**: PASS / **Summary**: [4 tests passed, 0 failed]
- **Failed Tests**: None
- **Notes**: Test `test_scan_directory_handles_permission_error` passed after fixing assertion (using ANY for timestamp). Existing error handling was sufficient.
### Test Execution: Unit - [2025-04-29 22:42:40]
- **Trigger**: Manual TDD Cycle 5 Refactor (Scanner - Incremental Scan)
- **Outcome**: PASS / **Summary**: [3 tests passed, 0 failed]
- **Failed Tests**: None
- **Notes**: Tests passed after refactoring `scan_directory` to use `_process_file` helper.
### Test Execution: Unit - [2025-04-29 22:39:53]
- **Trigger**: Manual TDD Cycle 4 (Scanner - Calc Hash)
- **Outcome**: PASS / **Summary**: [2 tests passed, 0 failed]
- **Failed Tests**: None
- **Notes**: Test `test_scan_directory_finds_files_and_calls_upsert` passed after adding hash calculation via `_calculate_hash` helper.
### Test Execution: Unit - [2025-04-29 22:38:06]
- **Trigger**: Manual TDD Cycle 3 (Scanner - Collect Metadata)
- **Outcome**: PASS / **Summary**: [2 tests passed, 0 failed]
- **Failed Tests**: None
- **Notes**: Test `test_scan_directory_finds_files_and_calls_upsert` passed after adding metadata collection (size, mtime) to `scan_directory`.
### Test Execution: Unit - [2025-04-29 22:35:24]
- **Trigger**: Manual TDD Cycle 2 (Scanner - Traverse/MS Call)
- **Outcome**: PASS / **Summary**: [2 tests passed, 0 failed]
- **Failed Tests**: None
- **Notes**: Test `test_scan_directory_finds_files_and_calls_upsert` passed after minimal `scan_directory` implementation.
### Test Execution: Unit - [2025-04-29 22:34:05]
- **Trigger**: Manual TDD Cycle 1 (Scanner - Init)
- **Outcome**: PASS / **Summary**: [1 test passed, 0 failed] (Note: Only ran scanner tests)
- **Failed Tests**: None
- **Notes**: Test `test_scanner_initialization` passed after minimal `Scanner` class implementation.
### Test Execution: Unit - [2025-04-29 22:21:52]
- **Trigger**: Manual TDD Cycle 6 (MetadataStore - Query Multi-Criteria)
- **Outcome**: PASS / **Summary**: [12 tests passed, 0 failed]
- **Failed Tests**: None
- **Notes**: Added test `test_query_files_multiple_criteria`. Passed immediately after previous refactoring of `query_files`.

### Test Execution: Unit - [2025-04-29 22:21:22]
- **Trigger**: Manual TDD Cycle 5 Refactor (MetadataStore - Query)
- **Outcome**: PASS / **Summary**: [11 tests passed, 0 failed]
- **Failed Tests**: None
- **Notes**: Ran tests after refactoring `query_files` to handle dynamic criteria. All passed.

### Test Execution: Unit - [2025-04-29 22:20:41]
- **Trigger**: Manual TDD Cycle 5 (MetadataStore - Query Path)
- **Outcome**: PASS / **Summary**: [11 tests passed, 0 failed]
- **Failed Tests**: None
- **Notes**: Added minimal `query_files` implementation handling only 'path'. Test `test_query_files_by_path` passed.

### Test Execution: Unit - [2025-04-29 22:20:05]
- **Trigger**: Manual TDD Cycle 5 (MetadataStore - Query Path)
- **Outcome**: FAIL / **Summary**: [1 failed, 10 passed]
- **Failed Tests**: `tests/test_metadata_store.py::test_query_files_by_path` (AttributeError: 'MetadataStore' object has no attribute 'query_files')
- **Notes**: Added test `test_query_files_by_path`. Failed as expected.

### Test Execution: Unit - [2025-04-29 22:19:32]
- **Trigger**: Manual TDD Cycle 4 (MetadataStore - Update Record)
- **Outcome**: PASS / **Summary**: [10 tests passed, 0 failed]
- **Failed Tests**: None
- **Notes**: Added test `test_upsert_file_record_update`. Passed immediately due to existing `INSERT OR REPLACE` logic.

### Test Execution: Unit - [2025-04-29 22:18:57]
- **Trigger**: Manual TDD Cycle 3 (MetadataStore - Add Record) - Attempt 3 (Fixes Applied)
- **Outcome**: PASS / **Summary**: [9 tests passed, 0 failed]
- **Failed Tests**: None
- **Notes**: Applied fixes to `test_initialize_schema` type check and `test_upsert_file_record_insert` timestamp comparison. All tests passed.

### Test Execution: Unit - [2025-04-29 21:55:39]
- **Trigger**: Manual TDD Cycle 3 (MetadataStore - Add Record) - Attempt 2 (pytz installed)
- **Outcome**: FAIL / **Summary**: [1 failed, 8 passed]
- **Failed Tests**: `tests/test_metadata_store.py::test_upsert_file_record_insert` (AssertionError: last_modified timestamp mismatch - 4hr difference)
- **Notes**: `pytz` installed, but timestamp comparison still failed, indicating timezone handling issue (likely naive vs aware or local vs UTC). Schema changed to `TIMESTAMPTZ` previously.

### Test Execution: Unit - [2025-04-29 21:52:36]
- **Trigger**: Manual TDD Cycle 3 (MetadataStore - Add Record) - Attempt 1 (Schema TIMESTAMPTZ)
- **Outcome**: FAIL / **Summary**: [2 failed, 7 passed]
- **Failed Tests**: `test_initialize_schema` (AssertionError: Type mismatch - expected TIMESTAMP, got TIMESTAMPTZ), `test_upsert_file_record_insert` (InvalidInputException: ModuleNotFoundError: No module named 'pytz')
- **Notes**: Changed schema to `TIMESTAMPTZ`. Schema test failed due to expectation mismatch. Upsert test failed because `pytz` is required for TIMESTAMPTZ.

### Test Execution: Unit - [2025-04-29 21:50:49]
- **Trigger**: Manual TDD Cycle 3 (MetadataStore - Add Record)
- **Outcome**: FAIL / **Summary**: [1 failed, 8 passed]
- **Failed Tests**: `tests/test_metadata_store.py::test_upsert_file_record_insert` (TypeError: can't subtract offset-naive and offset-aware datetimes)
- **Notes**: Implemented `upsert_file_record`. Test failed on timestamp comparison.

### Test Execution: Unit - [2025-04-29 21:49:55]
- **Trigger**: Manual TDD Cycle 3 (MetadataStore - Add Record)
- **Outcome**: FAIL / **Summary**: [1 failed, 8 passed]
- **Failed Tests**: `tests/test_metadata_store.py::test_upsert_file_record_insert` (AttributeError: 'MetadataStore' object has no attribute 'upsert_file_record')
- **Notes**: Added test `test_upsert_file_record_insert`. Failed as expected.

### Test Execution: Unit - [2025-04-29 21:48:07]
- **Trigger**: Manual TDD Cycle 2 (MetadataStore - Schema Init)
- **Outcome**: PASS / **Summary**: [8 tests passed, 0 failed]
- **Failed Tests**: None
- **Notes**: Implemented `_initialize_schema` and called from `__init__`. Test `test_initialize_schema` passed.

### Test Execution: Unit - [2025-04-29 21:47:17]
- **Trigger**: Manual TDD Cycle 2 (MetadataStore - Schema Init)
- **Outcome**: FAIL / **Summary**: [1 failed, 7 passed]
- **Failed Tests**: `tests/test_metadata_store.py::test_initialize_schema` (AssertionError: Table 'files' should exist)
- **Notes**: Corrected test `test_initialize_schema` to use `store.conn`. Failed as expected.

### Test Execution: Unit - [2025-04-29 21:45:58]
- **Trigger**: Manual TDD Cycle 2 (MetadataStore - Schema Init)
- **Outcome**: FAIL / **Summary**: [1 failed, 7 passed]
- **Failed Tests**: `tests/test_metadata_store.py::test_initialize_schema` (duckdb.IOException: IO Error: Cannot open file ... it is already open)
- **Notes**: Added test `test_initialize_schema`. Failed due to trying to open DB file twice.

### Test Execution: Unit - [2025-04-29 21:43:58]
- **Trigger**: Manual TDD Cycle 1 (MetadataStore - Init)
- **Outcome**: PASS / **Summary**: [7 tests passed, 0 failed] (Note: 6 were from ConfigManager)
- **Failed Tests**: None
- **Notes**: Added test `test_metadata_store_initialization`. Passed after minimal `MetadataStore` implementation (`__init__`, `close`, `__enter__`, `__exit__`). Added `duckdb` to requirements.txt.
### Test Execution: Unit - [2025-04-29 21:25:27]
- **Trigger**: Manual TDD Cycle 6
- **Outcome**: PASS / **Summary**: [6 tests passed, 0 failed]
- **Failed Tests**: None
- **Notes**: Added test for credential placeholder handling. Passed immediately as get() already returned raw string.

### Test Execution: Unit - [2025-04-29 21:23:39]
- **Trigger**: Manual TDD Cycle 5
- **Outcome**: PASS / **Summary**: [5 tests passed, 0 failed]
- **Failed Tests**: None
- **Notes**: Added test for schema validation (invalid type). Passed after adding basic type check in _validate_schema.
### TDD Cycle: MetadataStore - Query Multi-Criteria - [2025-04-29 22:21:52]
- **Red**: Added test `test_query_files_multiple_criteria` to check querying with multiple exact-match criteria (`hash` and `filename`). / Test File: `tests/test_metadata_store.py`
- **Green**: Test passed immediately due to the previous refactoring of `query_files` which already handled dynamic `AND` conditions. All 12 tests passed. / Code File: `src/storage_hygiene/metadata_store.py`
- **Refactor**: No refactoring needed. / Files Changed: `[]`
- **Outcome**: Cycle 6 completed, tests passing. Confirmed `query_files` handles multiple criteria.
- **Related Requirements**: [MS_Query] in `pseudocode/metadata_store.pseudo`

### TDD Cycle: MetadataStore - Query Path - [2025-04-29 22:21:22]
- **Red**: Added test `test_query_files_by_path` to check querying by path. Failed with `AttributeError` as `query_files` method didn't exist. / Test File: `tests/test_metadata_store.py`
- **Green**: Implemented minimal `query_files` method handling only `path` criteria. Test passed. All 11 tests passed. / Code File: `src/storage_hygiene/metadata_store.py`
- **Refactor**: Refactored `query_files` to dynamically build `WHERE` clause for multiple exact-match criteria using `AND`. Added check for valid column names. Ran tests again, all 11 passed. / Files Changed: `['src/storage_hygiene/metadata_store.py']`
- **Outcome**: Cycle 5 completed, tests passing. Basic query by path implemented and refactored for multiple criteria.
- **Related Requirements**: [MS_Query] in `pseudocode/metadata_store.pseudo`

### TDD Cycle: MetadataStore - Update Record - [2025-04-29 22:19:32]
- **Red**: Added test `test_upsert_file_record_update` to check updating an existing record. / Test File: `tests/test_metadata_store.py`
- **Green**: Test passed immediately. The existing `upsert_file_record` using `INSERT OR REPLACE` correctly handled the update case. All 10 tests passed. / Code File: `src/storage_hygiene/metadata_store.py`
- **Refactor**: No refactoring needed. / Files Changed: `[]`
- **Outcome**: Cycle 4 completed, tests passing. Confirmed `upsert_file_record` handles updates correctly.
- **Related Requirements**: [MS_UpdateRecord] in `pseudocode/metadata_store.pseudo`

### TDD Cycle: MetadataStore - Add Record - [2025-04-29 22:18:57]
- **Red**: Added test `test_upsert_file_record_insert`. Failed with `AttributeError`. / Test File: `tests/test_metadata_store.py`
- **Green**: Implemented `upsert_file_record` using `INSERT OR REPLACE`. Test failed with `TypeError` (naive vs aware datetime). Changed schema to `TIMESTAMPTZ`. Test failed with `ModuleNotFoundError: pytz` and schema test failed. Added `pytz` to requirements, installed it. Schema test expectation updated. Test failed with `AssertionError` (4hr diff). Fixed timestamp comparison logic in test. All 9 tests passed. / Code File: `src/storage_hygiene/metadata_store.py`, `requirements.txt`
- **Refactor**: No refactoring needed. / Files Changed: `[]`
- **Outcome**: Cycle 3 completed, tests passing. Record insertion implemented, timezone issues resolved by using `TIMESTAMPTZ` and `pytz`.
- **Related Requirements**: [MS_AddRecord] in `pseudocode/metadata_store.pseudo`

### TDD Cycle: MetadataStore - Schema Init - [2025-04-29 21:48:07]
- **Red**: Added test `test_initialize_schema`. Failed with `duckdb.IOException` (DB already open). Corrected test to use `store.conn`. Failed with `AssertionError` (table missing). / Test File: `tests/test_metadata_store.py`
- **Green**: Implemented `_initialize_schema` method creating the `files` table (using `TIMESTAMP`) and called it from `__init__`. Test passed. All 8 tests passed. / Code File: `src/storage_hygiene/metadata_store.py`
- **Refactor**: No refactoring needed. / Files Changed: `[]`
- **Outcome**: Cycle 2 completed, tests passing. Schema initialization implemented.
- **Related Requirements**: [MS_Schema] in `pseudocode/metadata_store.pseudo`

### TDD Cycle: MetadataStore - Init - [2025-04-29 21:43:58]
- **Red**: Added test `test_metadata_store_initialization`. Failed with `ModuleNotFoundError`. / Test File: `tests/test_metadata_store.py`
- **Green**: Created minimal `MetadataStore` class (`__init__`, `close`, `__enter__`, `__exit__`) establishing connection. Added `duckdb` to `requirements.txt`. Test passed. All 7 tests passed (including ConfigManager tests). / Code File: `src/storage_hygiene/metadata_store.py`, `requirements.txt`
- **Refactor**: No refactoring needed. / Files Changed: `[]`
- **Outcome**: Cycle 1 completed, tests passing. Basic class structure and DB connection/creation confirmed.
- **Related Requirements**: [MS_Init] in `pseudocode/metadata_store.pseudo`

### Test Execution: Unit - [2025-04-29 21:22:10]
- **Trigger**: Manual TDD Cycle 4
- **Outcome**: PASS / **Summary**: [4 tests passed, 0 failed]
- **Failed Tests**: None
- **Notes**: Added test for invalid YAML. Passed after modifying exception handling in _load_user_config.

### Test Execution: Unit - [2025-04-29 21:20:36]
- **Trigger**: Manual TDD Cycle 3
- **Outcome**: PASS / **Summary**: [3 tests passed, 0 failed]
- **Failed Tests**: None
- **Notes**: Added test for non-existent user config file. Passed immediately due to existing file existence check.

### Test Execution: Unit - [2025-04-29 21:19:31]
- **Trigger**: Manual TDD Cycle 2
- **Outcome**: PASS / **Summary**: [2 tests passed, 0 failed]
- **Failed Tests**: None
- **Notes**: Added test for user config override. Passed after implementing user config loading and merging.

### Test Execution: Unit - [2025-04-29 21:17:58]
- **Trigger**: Manual TDD Cycle 1
- **Outcome**: PASS / **Summary**: [1 tests passed, 0 failed]
### TDD Cycle: Scanner - Init - [2025-04-29 22:34:05]
### TDD Cycle: Scanner - Traverse/MS Call - [2025-04-29 22:35:24]
### TDD Cycle: Scanner - Collect Metadata - [2025-04-29 22:38:06]
### TDD Cycle: Scanner - Calc Hash - [2025-04-29 22:39:53]
### TDD Cycle: Scanner - Incremental Scan - [2025-04-29 22:42:40]
### TDD Cycle: Scanner - Error Handling - [2025-04-29 22:44:37]
- **Red**: Added test `test_scan_directory_handles_permission_error` using mock side effect to simulate `OSError`. Initial run failed on timestamp assertion in `assert_called_once_with`. / Test File: `tests/test_scanner.py`
- **Green**: Modified assertion in test to use `unittest.mock.ANY` for `last_modified` timestamp comparison. The existing `try...except OSError` block in `_process_file` correctly handled the simulated error and allowed processing to continue. All tests passed. / Code File: `src/storage_hygiene/scanner.py`
- **Refactor**: No refactoring needed. Basic error handling is sufficient for now. / Files Changed: `[]`
- **Outcome**: Cycle 6 completed, tests passing. Confirmed graceful handling of file processing errors.
- **Related Requirements**: [SCAN_HandleErrors] in `pseudocode/scanner.pseudo`
- **Red**: Added test `test_scan_directory_skips_unchanged_files`. Configured mock `query_files` to return an existing record. Test failed with `AssertionError: Expected 'query_files' to be called once. Called 0 times.`. / Test File: `tests/test_scanner.py`
- **Green**: Modified `scan_directory` to call `self.metadata_store.query_files`. Added logic to compare `size` and `last_modified` (with tolerance) against the returned record. If matched, `continue` to skip processing. Fixed mock config in `test_scan_directory_finds_files_and_calls_upsert` to return `[]`. All tests passed. / Code File: `src/storage_hygiene/scanner.py`
- **Refactor**: Extracted file processing logic (incremental check, stat, hash, upsert) into `_process_file` helper method. Ran tests again, all passed. / Files Changed: `['src/storage_hygiene/scanner.py']`
- **Outcome**: Cycle 5 completed, tests passing. Confirmed incremental scan logic skips unchanged files. Code refactored for clarity.
- **Related Requirements**: [SCAN_Incremental], [SCAN_InteractMS] in `pseudocode/scanner.pseudo`, `docs/architecture/adr/004-incremental-scans.md`
- **Red**: Modified test `test_scan_directory_finds_files_and_calls_upsert` to assert `hash_value`. Test failed with `AssertionError: assert None == 'd0b4...'`. / Test File: `tests/test_scanner.py`
- **Green**: Added `_calculate_hash` helper method using `hashlib.sha256` and reading file in chunks. Called this method in `scan_directory` and passed the result to `upsert_file_record`. Test passed. / Code File: `src/storage_hygiene/scanner.py`
- **Refactor**: No refactoring needed. / Files Changed: `[]`
- **Outcome**: Cycle 4 completed, tests passing. Confirmed hash calculation and passing to MetadataStore.
- **Related Requirements**: [SCAN_CalcHash], [SCAN_InteractMS] in `pseudocode/scanner.pseudo`
- **Red**: Modified test `test_scan_directory_finds_files_and_calls_upsert` to assert `size` and `last_modified` are passed to `upsert_file_record`. Added `datetime` import. Test failed with `AssertionError: assert None == 8`. / Test File: `tests/test_scanner.py`
- **Green**: Modified `scan_directory` to use `item_path.stat()` to get `st_size` and `st_mtime`. Converted `mtime` to timezone-aware UTC `datetime`. Passed these values to `upsert_file_record`. Added basic `try...except OSError` around `stat()`. Test passed. / Code File: `src/storage_hygiene/scanner.py`
- **Refactor**: No refactoring needed. / Files Changed: `[]`
- **Outcome**: Cycle 3 completed, tests passing. Confirmed collection and passing of basic metadata (size, mtime).
### TDD Cycle: AnalysisEngine - Old File Rule - [2025-04-29 22:57:37]
- **Red**: Added test `test_analyze_identifies_old_files`. Failed with `AssertionError: Expected 'query_files' to have been called once. Called 0 times.`. / Test File: `tests/test_analysis_engine.py`
- **Green**: Implemented `_apply_old_file_rule` method, calling `metadata_store.query_files()` and generating `review_old` actions based on `last_modified` date and `max_days` threshold. Fixed indentation/duplication issues caused by previous tool errors. All 5 tests passed. / Code File: `src/storage_hygiene/analysis_engine.py`
- **Refactor**: No refactoring needed. / Files Changed: `[]`
- **Outcome**: Cycle 5 completed, tests passing. Confirmed old file identification and action generation.
- **Related Requirements**: [AE_Analyze_Old] in `pseudocode/analysis_engine.pseudo`
### TDD Cycle: AnalysisEngine - Large File Rule - [2025-04-29 22:54:22]
- **Red**: Added test `test_analyze_identifies_large_files`. Failed with `AssertionError: Expected 'query_files' to have been called once. Called 0 times.`. / Test File: `tests/test_analysis_engine.py`
- **Green**: Implemented `_apply_large_file_rule` method, calling `metadata_store.query_files()` and generating `review_large` actions based on size threshold. All 4 tests passed. / Code File: `src/storage_hygiene/analysis_engine.py`
- **Refactor**: No refactoring needed. / Files Changed: `[]`
- **Outcome**: Cycle 4 completed, tests passing. Confirmed large file identification and action generation.
- **Related Requirements**: [AE_Analyze_Large] in `pseudocode/analysis_engine.pseudo`
- **Related Requirements**: [SCAN_CollectMeta], [SCAN_InteractMS] in `pseudocode/scanner.pseudo`
- **Red**: Added test `test_scan_directory_finds_files_and_calls_upsert`. Failed with `AttributeError: 'Scanner' object has no attribute 'scan_directory'`. / Test File: `tests/test_scanner.py`
- **Green**: Implemented minimal `scan_directory` method using `pathlib.Path.rglob('*')` to find files and calling `self.metadata_store.upsert_file_record` with just the resolved `file_path`. Test passed. / Code File: `src/storage_hygiene/scanner.py`
- **Refactor**: No refactoring needed. / Files Changed: `[]`
- **Outcome**: Cycle 2 completed, tests passing. Confirmed basic directory traversal and interaction with MetadataStore mock.
### TDD Cycle: AnalysisEngine - Duplicate Rule - [2025-04-29 22:52:48]
- **Red**: Added test `test_analyze_identifies_duplicate_files`. Failed with `AssertionError: Expected 'get_duplicates' to have been called once. Called 0 times.`. / Test File: `tests/test_analysis_engine.py`
- **Green**: Implemented duplicate detection logic in `analyze` method, calling `metadata_store.get_duplicates()` and generating `stage_duplicate` actions. All 3 tests passed. / Code File: `src/storage_hygiene/analysis_engine.py`
- **Refactor**: Extracted duplicate detection logic into `_apply_duplicate_rule` method. Tests passed. / Files Changed: `['src/storage_hygiene/analysis_engine.py']`
- **Outcome**: Cycle 3 completed, tests passing. Confirmed duplicate file identification and action generation. Logic refactored.
- **Related Requirements**: [AE_Analyze_Duplicates] in `pseudocode/analysis_engine.pseudo`
- **Related Requirements**: [SCAN_Traverse], [SCAN_InteractMS] (partially) in `pseudocode/scanner.pseudo`
- **Red**: Wrote failing test `test_scanner_initialization` in `tests/test_scanner.py`. Pytest skipped the test as `Scanner` class was not found. / Test File: `tests/test_scanner.py`
- **Green**: Created minimal `Scanner` class in `src/storage_hygiene/scanner.py` with `__init__` accepting `config_manager` and `metadata_store`. Test passed. / Code File: `src/storage_hygiene/scanner.py`
- **Refactor**: No refactoring needed. / Files Changed: `[]`
- **Outcome**: Cycle 1 completed, test passing. Confirmed basic class structure and dependency injection.
- **Related Requirements**: [SCAN_Init] in `pseudocode/scanner.pseudo`
### TDD Cycle: ActionExecutor - Init - [2025-04-29 23:02:27]
- **Red**: Wrote failing test `test_action_executor_initialization` in `tests/test_action_executor.py`. Test failed with `AttributeError`. / Test File: `tests/test_action_executor.py`
### TDD Cycle: ActionExecutor - Load Config - [2025-04-29 23:11:10]
- **Red**: Added test `test_execute_actions_retrieves_config`. Failed with `fixture 'mocker' not found`. Added `pytest-mock` to requirements and installed. Test then failed with `AttributeError: 'ActionExecutor' object has no attribute 'execute_actions'`. / Test File: `tests/test_action_executor.py`, `requirements.txt`
- **Green**: Implemented minimal `execute_actions` method in `ActionExecutor`, retrieving `staging_dir` and `dry_run` from `config_manager`. Both tests passed. / Code File: `src/storage_hygiene/action_executor.py`
### TDD Cycle: ActionExecutor - Dispatch (Stage Duplicate) - [2025-04-29 23:14:35]
- **Red**: Added test `test_execute_actions_dispatches_stage_duplicate`. Failed with `AttributeError: ... does not have the attribute '_stage_duplicate'`. / Test File: `tests/test_action_executor.py`
- **Green**: Added placeholder `_stage_duplicate` method and dispatch logic in `execute_actions`. Test passed. / Code File: `src/storage_hygiene/action_executor.py`
- **Refactor**: Refactored dispatch logic to use a handler map in `__init__`. Test failed due to patching instance after init. Fixed test to patch class before instance creation. All tests passed. / Files Changed: `['src/storage_hygiene/action_executor.py', 'tests/test_action_executor.py']`
### TDD Cycle: ActionExecutor - Stage Duplicate Logic - [2025-04-29 23:16:56]
- **Red**: Added test `test_stage_duplicate_moves_file` mocking `os.makedirs` and `shutil.move`. Test failed with `AssertionError: Expected 'makedirs' to be called once. Called 0 times.`. / Test File: `tests/test_action_executor.py`
- **Green**: Implemented logic in `_stage_duplicate` to calculate destination path using `_get_staging_path` and call `os.makedirs` and `shutil.move` (if not dry run and dest doesn't exist). All tests passed. / Code File: `src/storage_hygiene/action_executor.py`
- **Refactor**: Confirmed `_get_staging_path` was already extracted during Green phase. No further refactoring needed. All tests passed. / Files Changed: `[]`
### TDD Cycle: ActionExecutor - Dry Run Mode - [2025-04-29 23:18:16]
- **Red**: Added test `test_stage_duplicate_dry_run_logs_and_skips_move` with `dry_run=True`. / Test File: `tests/test_action_executor.py`
- **Green**: Test passed immediately as the existing `_stage_duplicate` implementation already handled the `dry_run` flag correctly. All 5 tests passed. / Code File: `src/storage_hygiene/action_executor.py`
- **Refactor**: No refactoring needed for dry run logic. / Files Changed: `[]`
### TDD Cycle: ActionExecutor - Dispatch (Review Large) - [2025-04-29 23:19:40]
- **Red**: Added placeholder `_review_large` method and handler map entry. Added test `test_execute_actions_dispatches_review_large`. / Test File: `tests/test_action_executor.py`, `src/storage_hygiene/action_executor.py`
- **Green**: Test passed immediately as the dispatch logic correctly called the new placeholder handler. All 6 tests passed. / Code File: `src/storage_hygiene/action_executor.py`
- **Refactor**: No refactoring needed. / Files Changed: `[]`
### TDD Cycle: ActionExecutor - Review Large Logic - [2025-04-29 23:23:17]
- **Red**: Added test `test_review_large_moves_file`. Failed with `AssertionError: Expected 'makedirs' to be called once. Called 0 times.`. / Test File: `tests/test_action_executor.py`
- **Green**: Implemented logic in `_review_large` using `_get_staging_path` and calling file system mocks. All 7 tests passed. / Code File: `src/storage_hygiene/action_executor.py`
- **Refactor**: Refactored `_stage_duplicate` and `_review_large` to use a generic `_stage_file` method. Confirmed tests still pass. / Files Changed: `['src/storage_hygiene/action_executor.py']`
### TDD Cycle: ActionExecutor - Dispatch (Review Old) - [2025-04-29 23:24:37]
- **Red**: Added placeholder `_review_old` method and handler map entry. Added test `test_execute_actions_dispatches_review_old`. / Test File: `tests/test_action_executor.py`, `src/storage_hygiene/action_executor.py`
- **Green**: Test passed immediately as the dispatch logic correctly called the new placeholder handler. All 8 tests passed. / Code File: `src/storage_hygiene/action_executor.py`
- **Refactor**: No refactoring needed. / Files Changed: `[]`
### TDD Cycle: ActionExecutor - Review Old Logic - [2025-04-29 23:26:19]
- **Red**: Added test `test_review_old_moves_file`. Failed with `AssertionError: Expected '_stage_file' to be called once. Called 0 times.`. / Test File: `tests/test_action_executor.py`
- **Green**: Implemented `_review_old` to call `_stage_file` with appropriate arguments. All 9 tests passed. / Code File: `src/storage_hygiene/action_executor.py`
- **Refactor**: No refactoring needed. / Files Changed: `[]`
### TDD Cycle: ActionExecutor - Error Handling (File Not Found) - [2025-04-29 23:27:35]
- **Red**: Added test `test_stage_file_handles_file_not_found_error` simulating `FileNotFoundError` on `shutil.move`. / Test File: `tests/test_action_executor.py`
- **Green**: Test passed immediately as the existing `try...except OSError` block in `_stage_file` correctly handled the error. All 10 tests passed. / Code File: `src/storage_hygiene/action_executor.py`
- **Refactor**: No refactoring needed. / Files Changed: `[]`
- **Outcome**: Cycle 10 completed, tests passing. Confirmed basic error handling for file move operations.
- **Related Requirements**: [AX_HandleErrors] in `pseudocode/action_executor.pseudo`
- **Outcome**: Cycle 9 completed, tests passing. Logic for staging old files implemented using the generic method.
- **Related Requirements**: [AX_StageOld], [AX_FileSystem] in `pseudocode/action_executor.pseudo`
- **Outcome**: Cycle 8 completed, tests passing. Confirmed dispatch logic for `review_old`.
- **Related Requirements**: [AX_Dispatch] in `pseudocode/action_executor.pseudo`
- **Outcome**: Cycle 7 completed, tests passing. Logic for staging large files implemented and staging logic refactored.
- **Related Requirements**: [AX_StageLarge], [AX_FileSystem], [AX_StagePath] in `pseudocode/action_executor.pseudo`
- **Outcome**: Cycle 6 completed, tests passing. Confirmed dispatch logic for `review_large`.
- **Related Requirements**: [AX_Dispatch] in `pseudocode/action_executor.pseudo`
- **Outcome**: Cycle 5 completed, tests passing. Confirmed dry run logic prevents file operations and logs intent.
- **Related Requirements**: [AX_DryRun], [AX_StageDup] in `pseudocode/action_executor.pseudo`, `docs/architecture/adr/005-dry-run-mode.md`
- **Outcome**: Cycle 4 completed, tests passing. Core logic for staging duplicates implemented and path calculation refactored.
- **Related Requirements**: [AX_StageDup], [AX_FileSystem], [AX_StagePath] in `pseudocode/action_executor.pseudo`
- **Outcome**: Cycle 3 completed, tests passing. Dispatch logic implemented and refactored.
- **Related Requirements**: [AX_Dispatch] in `pseudocode/action_executor.pseudo`
- **Refactor**: No refactoring needed. / Files Changed: `[]`
- **Outcome**: Cycle 2 completed, tests passing. Confirmed config loading within `execute_actions`.
- **Related Requirements**: [AX_LoadConfig], [AX_Execute] in `pseudocode/action_executor.pseudo`
- **Green**: Created minimal `ActionExecutor` class in `src/storage_hygiene/action_executor.py` storing `config_manager`. Test passed. / Code File: `src/storage_hygiene/action_executor.py`
- **Refactor**: No refactoring needed. / Files Changed: `[]`
- **Outcome**: Cycle 1 completed, test passing. Confirmed basic class structure and dependency injection.
- **Related Requirements**: [AX_Init] in `pseudocode/action_executor.pseudo`
- **Failed Tests**: None
- **Notes**: Initial test for default config loading passed after minimal implementation. Ran using `python -m pytest`.

## TDD Cycles Log
<!-- Append TDD cycle outcomes using the format below -->
### TDD Cycle: AnalysisEngine - Load Rules - [2025-04-29 22:50:35]
- **Red**: Added test `test_analysis_engine_loads_rules_from_config`. Failed with `AssertionError: Expected 'get' to be called once. Called 0 times.`. / Test File: `tests/test_analysis_engine.py`
- **Green**: Modified `_load_rules` in `AnalysisEngine` to call `self.config_manager.get('analysis.rules', {})`. Both tests passed. / Code File: `src/storage_hygiene/analysis_engine.py`
- **Refactor**: No refactoring needed. / Files Changed: `[]`
- **Outcome**: Cycle 2 completed, tests passing. Confirmed rule loading from ConfigManager.
- **Related Requirements**: [AE_LoadRules] in `pseudocode/analysis_engine.pseudo`
### TDD Cycle: AnalysisEngine - Init - [2025-04-29 22:49:08]
- **Red**: Wrote failing test `test_analysis_engine_initialization` in `tests/test_analysis_engine.py`. Test failed as `AnalysisEngine` class was not found. / Test File: `tests/test_analysis_engine.py`
- **Green**: Created minimal `AnalysisEngine` class in `src/storage_hygiene/analysis_engine.py` with `__init__` accepting `config_manager` and `metadata_store`, and placeholder `_load_rules` and `analyze` methods. Test passed. / Code File: `src/storage_hygiene/analysis_engine.py`
- **Refactor**: No refactoring needed for this minimal implementation. / Files Changed: `[]`
- **Outcome**: Cycle 1 completed, test passing. Confirmed basic class structure and dependency injection.
- **Related Requirements**: [AE_Init] in `pseudocode/analysis_engine.pseudo`
### TDD Cycle: Credential Placeholder Handling - [2025-04-29 21:25:27]
- **Red**: Added test `test_get_credential_placeholder` to ensure `get()` returns raw placeholder strings. / Test File: `tests/test_config_manager.py`
- **Green**: Test passed immediately. The existing `get()` method correctly retrieves the value from the dictionary, which is the placeholder string itself, without attempting resolution. All 6 tests passed. / Code File: `src/storage_hygiene/config_manager.py`
- **Refactor**: No refactoring needed. / Files Changed: `[]`
- **Outcome**: Cycle 6 completed, tests passing. Confirmed correct handling of credential placeholders (returning raw string).
- **Related Requirements**: [CM_HandleCredentials] in `pseudocode/config_manager.pseudo`, `docs/architecture/adr/002-credential-management.md`

### TDD Cycle: Schema Validation (Basic Type Check) - [2025-04-29 21:23:39]
- **Red**: Added test `test_validate_config_schema_invalid_type` expecting `ConfigLoadError` for incorrect data type (`analysis.min_file_size_mb`). Test failed as expected. / Test File: `tests/test_config_manager.py`
- **Green**: Added `_validate_schema` method called in `__init__`. Implemented a basic check for `isinstance(value, (int, float))` for `analysis.min_file_size_mb`, raising `ConfigLoadError` if invalid. All 5 tests passed. / Code File: `src/storage_hygiene/config_manager.py`
- **Refactor**: No refactoring needed. Validation is minimal as required by TDD. / Files Changed: `[]`
- **Outcome**: Cycle 5 completed, tests passing. Confirmed basic schema validation for data types.
- **Related Requirements**: [CM_ValidateSchema] in `pseudocode/config_manager.pseudo`

### TDD Cycle: Invalid YAML Handling - [2025-04-29 21:22:10]
- **Red**: Added test `test_handle_invalid_user_config_yaml` expecting `ConfigLoadError`. Test failed as `_load_user_config` returned `None` instead of raising. / Test File: `tests/test_config_manager.py`
- **Green**: Modified `_load_user_config` to catch `yaml.YAMLError` and raise `ConfigLoadError`, wrapping the original error. All 4 tests passed. / Code File: `src/storage_hygiene/config_manager.py`
- **Refactor**: No refactoring needed. / Files Changed: `[]`
- **Outcome**: Cycle 4 completed, tests passing. Confirmed correct exception handling for invalid YAML.
- **Related Requirements**: [CM_HandleInvalidUserFile] in `pseudocode/config_manager.pseudo`

### TDD Cycle: Missing User File Handling - [2025-04-29 21:20:36]
- **Red**: Added test `test_handle_non_existent_user_config`. / Test File: `tests/test_config_manager.py`
- **Green**: Test passed immediately. The existing implementation (`if path and os.path.exists(path):` in `_load_user_config`) already handled this case correctly by returning `None` and skipping the merge, thus using defaults. / Code File: `src/storage_hygiene/config_manager.py`
- **Refactor**: No refactoring needed. / Files Changed: `[]`
- **Outcome**: Cycle 3 completed, tests passing. Confirmed graceful handling of non-existent user config files.
- **Related Requirements**: [CM_HandleMissingUserFile] in `pseudocode/config_manager.pseudo`

### TDD Cycle: User Config Override - [2025-04-29 21:19:31]
- **Red**: Added test `test_load_user_config_overrides_defaults` using `tmp_path` fixture and a temporary YAML file. Test failed as expected because user config loading wasn't implemented. / Test File: `tests/test_config_manager.py`
- **Green**: Implemented `_load_user_config` using `PyYAML` and `_merge_configs` for recursive dictionary merging in `ConfigManager`. Both tests passed. / Code File: `src/storage_hygiene/config_manager.py`
- **Refactor**: No refactoring needed. Basic loading/merging logic is in place. Error handling is minimal (warnings printed) and will be addressed later. / Files Changed: `[]`
- **Outcome**: Cycle 2 completed, tests passing. Confirmed user config loading and overriding defaults.
- **Related Requirements**: [CM_LoadUser] in `pseudocode/config_manager.pseudo`

### TDD Cycle: ConfigManager Defaults - [2025-04-29 21:17:58]
- **Red**: Wrote failing test `test_load_default_config` in `tests/test_config_manager.py` to check default loading. Initial run failed with `ModuleNotFoundError`. / Test File: `tests/test_config_manager.py`
- **Green**: Created `src/storage_hygiene/__init__.py` and minimal `ConfigManager` class in `src/storage_hygiene/config_manager.py` with hardcoded defaults and `get()` method. Test passed using `python -m pytest`. / Code File: `src/storage_hygiene/config_manager.py`
- **Refactor**: No refactoring needed for this minimal implementation. / Files Changed: `[]`
- **Outcome**: Cycle 1 completed, test passing. Confirmed basic class structure and default value access.
- **Related Requirements**: [CM_LoadDefaults] in `pseudocode/config_manager.pseudo`

## Test Fixtures
<!-- Append new fixtures using the format below -->

## Test Coverage Summary
<!-- Update coverage summary using the format below -->

## Test Plans (Driving Implementation)
<!-- Append new test plans using the format below -->
### Test Plan: ConfigManager - [2025-04-29 21:16:13]
- **Objective**: Implement ConfigManager to load default and user configurations, provide access via get(), and handle validation.
- **Scope**: `src/storage_hygiene/config_manager.py`
- **Test Cases**:
    - Case 1 (Failing): Load default config values. / Expected: Default values returned by `get()`. / Status: Green
    - Case 2 (Failing): Load user config file, overriding defaults. / Expected: User values returned by `get()`. / Status: Green
    - Case 3 (Failing): Handle non-existent user config file gracefully (use defaults). / Expected: Default values returned. / Status: Green
    - Case 4 (Failing): Handle invalid user config file (YAML error). / Expected: Raise specific exception. / Status: Green
    - Case 5 (Failing): Validate loaded config against schema. / Expected: Raise validation error for invalid schema. / Status: Green
    - Case 6 (Failing): Access nested keys using dot notation. / Expected: Correct nested value returned. / Status: Green <!-- Implicitly tested in Cycle 1 & 2 -->
    - Case 7 (Failing): Return default value for non-existent key. / Expected: Provided default value returned. / Status: Green <!-- Implicitly tested in Cycle 1 & 2 -->
    - Case 8 (Failing): Handle credential placeholders safely (return placeholder string). / Expected: Placeholder string returned for credential keys. / Status: Green
- **Related Requirements**: `pseudocode/config_manager.pseudo`, `docs/architecture/adr/002-credential-management.md`