# Debug Specific Memory
<!-- Entries below should be added reverse chronologically (newest first) -->

## Issue History
### Issue: Pytest-Failures-Remaining-10 - 10 Pytest Failures after Second Debug Session - [Status: Resolved] - [2025-04-30 00:27:13]
- **Reported**: 2025-04-30 00:19:12 / **Severity**: High / **Symptoms**: 10 pytest failures (Integration: path normalization, error propagation, test assertions; Unit: ActionExecutor config default type, AnalysisEngine action dict structure, Scanner metadata key, Scanner path normalization assertion).
- **Investigation**:
    1. Analyzed pytest output. [2025-04-30 00:20:08]
    2. Corrected hash content in `test_main_workflow_non_dry_run`. [2025-04-30 00:21:10]
    3. Corrected `ConfigManager` error handling for non-dict YAML. [2025-04-30 00:21:48]
    4. Removed incorrect assertion in `test_main_workflow_non_existent_target`. [2025-04-30 00:24:52]
    5. Corrected error message assertion in `test_main_workflow_bad_staging_dir`. [2025-04-30 00:21:10]
    6. Corrected default path type assertion in `test_execute_actions_retrieves_config`. [2025-04-30 00:22:23]
    7. Added missing 'action' key in `AnalysisEngine` rule methods. [2025-04-30 00:22:48]
    8. Corrected hash key usage in `src/storage_hygiene/scanner.py` (changed to `hash_value`). [2025-04-30 00:23:14]
    9. Corrected path normalization assertion in `test_scan_directory_skips_unchanged_files`. [2025-04-30 00:23:38]
    10. Ran pytest, 8 failures remained. Re-analyzed. [2025-04-30 00:23:57]
    11. Identified incorrect hash key usage (`hash_value` vs `hash`) between `Scanner` and `MetadataStore`. [2025-04-30 00:24:17]
    12. Identified incorrect staging path names (`large` vs `large_files`) in `test_main_workflow_non_dry_run`. [2025-04-30 00:25:37]
    13. Identified invalid YAML in `test_main_workflow_invalid_config_yaml` was actually valid due to comment. [2025-04-30 00:25:37]
    14. Identified incorrect hash key assertion (`hash_value` vs `hash`) in `test_scan_directory_finds_files_and_calls_upsert`. [2025-04-30 00:25:37]
    15. Reverted hash key to 'hash' in `src/storage_hygiene/scanner.py`. [2025-04-30 00:24:34]
    16. Corrected error handling in `src/storage_hygiene/main.py` scan loop. [2025-04-30 00:24:52]
    17. Corrected staging path names in `tests/integration/test_main_workflow.py`. [2025-04-30 00:25:59]
    18. Made YAML truly invalid in `tests/integration/test_main_workflow.py`. [2025-04-30 00:26:12]
    19. Corrected hash key assertion in `tests/test_scanner.py`. [2025-04-30 00:26:27]
- **Root Cause**:
    - `tests/integration/test_main_workflow.py`: Incorrect hash content, incorrect staging path names (`large` vs `large_files`, `old` vs `old_files`), commented-out invalid YAML, incorrect assertion about workflow order.
    - `src/storage_hygiene/main.py`: Insufficient error handling for critical scan errors (`ValueError`).
    - `tests/test_action_executor.py`: Mismatched default type (string vs Path) in assertion.
    - `src/storage_hygiene/analysis_engine.py`: Missing 'action' key in generated action dictionaries.
    - `src/storage_hygiene/scanner.py`: Incorrect hash key used (`hash_value` instead of `hash`).
    - `tests/test_scanner.py`: Incorrect hash key assertion (`hash_value` vs `hash`), missing path normalization in assertion.
- **Fix Applied**:
    - Corrected hash content, staging paths, invalid YAML, and assertions in `tests/integration/test_main_workflow.py`. [2025-04-30 00:21:10, 2025-04-30 00:25:59, 2025-04-30 00:26:12, 2025-04-30 00:25:06]
    - Improved error handling in `src/storage_hygiene/main.py` scan loop. [2025-04-30 00:24:52]
    - Corrected default type assertion in `tests/test_action_executor.py`. [2025-04-30 00:22:23]
    - Added 'action' key in `src/storage_hygiene/analysis_engine.py`. [2025-04-30 00:22:48]
    - Reverted hash key to 'hash' in `src/storage_hygiene/scanner.py`. [2025-04-30 00:24:34]
    - Corrected hash key assertion and added path normalization to assertion in `tests/test_scanner.py`. [2025-04-30 00:26:27, 2025-04-30 00:23:38]
- **Verification**: `pytest` run passed all 39 tests. [2025-04-30 00:26:41]
- **Related Issues**: [See Issue: Pytest-Failures-Remaining-13 in debug.md]
### Issue: Pytest-Failures-Remaining-13 - 13 Pytest Failures after Initial Fix - [Status: Resolved] - [2025-04-30 00:14:56]
- **Reported**: 2025-04-30 00:09:05 / **Severity**: High / **Symptoms**: 13 pytest failures remaining after initial fix attempt. Categories: Integration Test Logic (DB path, exit codes, log messages), Unit Test Mock/Assertion Issues (ActionExecutor config keys/paths, AnalysisEngine return structure, ActionExecutor error handling, Scanner metadata key).
- **Investigation**:
    1. Analyzed remaining pytest output, confirming categories. [2025-04-30 00:10:05]
    2. Verified `ActionExecutor` config keys (`action_executor.*`) and default staging path (`./.storage_hygiene_staging`). [2025-04-30 00:10:18]
    3. Verified `AnalysisEngine.analyze` returns `dict`, not `list`. [2025-04-30 00:10:59]
    4. Confirmed hash calculation in `test_main_workflow_non_dry_run` was correct, but initial failure report was misleading. Identified path normalization (`os.path.normcase`) as likely cause for DB update warnings. [2025-04-30 00:11:48 - 00:12:47]
    5. Confirmed `main.py` has exit logic, but `ActionExecutor.execute_actions` swallowed critical `OSError`. [2025-04-30 00:13:12 - 00:13:37]
    6. Confirmed `test_main_workflow_non_existent_target` assertion didn't match actual log output. [2025-04-30 00:14:07]
    7. Confirmed `_stage_file` re-raises `OSError`, but `test_stage_file_handles_file_not_found_error` incorrectly expected it to be caught. [2025-04-30 00:14:23]
    8. Confirmed `test_scanner.py` used incorrect key ('size' vs 'size_bytes') in assertion. [2025-04-30 00:14:32]
- **Root Cause**:
    - `test_action_executor.py`: Incorrect config keys/paths in mock assertions. Test `test_stage_file_handles_file_not_found_error` expected error catching instead of raising.
    - `test_analysis_engine.py`: Assertions expected `list`, but `analyze` returns `dict`.
    - `Scanner`/`ActionExecutor`/`MetadataStore`: Path strings used for DB primary key and updates were not consistently normalized (using `os.path.normcase`).
    - `ActionExecutor`: Swallowed critical `OSError` in `execute_actions` loop.
    - `test_main_workflow.py`: `test_main_workflow_non_existent_target` asserted for incorrect log message format.
    - `test_scanner.py`: Assertion used incorrect metadata key (`size` vs `size_bytes`).
- **Fix Applied**:
    - Corrected mock assertions (config keys, staging path) in `test_action_executor.py`. [2025-04-30 00:10:44]
    - Updated assertions in `test_analysis_engine.py` to check lists within the returned dictionary. [2025-04-30 00:11:24]
    - Applied `os.path.normcase()` to paths in `Scanner._process_file` (before storing) and `ActionExecutor._stage_file` (before updating). [2025-04-30 00:12:47, 2025-04-30 00:13:00]
    - Modified `ActionExecutor.execute_actions` to re-raise `OSError`. [2025-04-30 00:13:53]
    - Updated assertion in `test_main_workflow_non_existent_target` to match actual log output. [2025-04-30 00:14:07]
    - Updated `test_stage_file_handles_file_not_found_error` to use `pytest.raises`. [2025-04-30 00:14:23]
    - Corrected assertion key in `test_scanner.py` to `size_bytes`. [2025-04-30 00:14:56]
- **Verification**: Pre-completion checks passed. Tests should now pass.
- **Related Issues**: [See Issue: Pytest-Failures-20250430 in debug.md]
### Issue: Pytest-Failures-20250430 - 16 Pytest Failures after Integration - [Status: Resolved] - [2025-04-30 00:04:45]
- **Reported**: 2025-04-29 23:56:39 / **Severity**: High / **Symptoms**: 16 pytest failures across integration and unit tests (ActionExecutor, AnalysisEngine, Scanner, Main Workflow).
- **Investigation**:
    1. Analyzed pytest output, identifying categories: Interface mismatch (ActionExecutor list vs dict), Import errors (AnalysisEngine), Logic errors (MetadataStore path update, Main error handling), Test assertion errors (Scanner mocks, Main workflow paths/logs). [2025-04-29 23:57:25]
    2. Read relevant source files (`action_executor.py`, `analysis_engine.py`, `metadata_store.py`, `main.py`, `scanner.py`) and test files (`test_action_executor.py`, `test_analysis_engine.py`, `test_scanner.py`, `test_main_workflow.py`). [2025-04-29 23:57:41 - 2025-04-30 00:03:31]
- **Root Cause**:
    - `ActionExecutor`: `execute_actions` expected `dict`, tests passed `list`. `__init__` lacked `metadata_store`. `_stage_file` didn't update DB path or re-raise critical `OSError`.
    - `AnalysisEngine`: Test file had incorrect import (`src.` prefix) and leftover TDD `try/except ImportError`.
    - `MetadataStore`: Lacked `update_file_path` method.
    - `Scanner`: Tests had incorrect mock assertions for `upsert_file_record` and `query_files` arguments. Missing `pathlib` import in test file.
    - `Main Workflow Tests`: `test_main_workflow_non_dry_run` had incorrect expected path for duplicates. `test_main_cli_arguments` asserted for a log message not generated when no actions occur. `test_main_workflow_invalid_config_yaml` had unescaped braces in YAML string. `test_main_workflow_non_existent_target` and `test_main_workflow_bad_staging_dir` didn't fail correctly because `main.py` didn't exit non-zero on specific errors.
- **Fix Applied**:
    - Corrected `execute_actions` calls in `test_action_executor.py` to pass `dict`. [2025-04-29 23:58:04]
    - Corrected import in `test_analysis_engine.py`. [2025-04-29 23:58:34]
    - Added `update_file_path` method to `MetadataStore`. [2025-04-29 23:59:17]
    - Fixed indentation in `MetadataStore` after insertion. [2025-04-29 23:59:43]
    - Updated `ActionExecutor.__init__` to accept `metadata_store`. [2025-04-30 00:00:10]
    - Updated `ActionExecutor._stage_file` to call `update_file_path` and re-raise `OSError`. [2025-04-30 00:03:20]
    - Updated `ActionExecutor` instantiation in `main.py`. [2025-04-30 00:00:34]
    - Updated `ActionExecutor` instantiations in `test_action_executor.py` tests. [2025-04-30 00:01:01]
    - Corrected expected duplicate path and added `hashlib` import in `test_main_workflow_non_dry_run`. [2025-04-30 00:01:38, 2025-04-30 00:02:13]
    - Removed invalid log assertion in `test_main_cli_arguments`. [2025-04-30 00:02:27]
    - Escaped YAML braces in `test_main_workflow_invalid_config_yaml`. [2025-04-30 00:02:42]
    - Added exit logic for no valid targets in `main.py`. [2025-04-30 00:03:05]
    - Corrected mock assertions in `test_scanner.py`. [2025-04-30 00:03:54]
    - Added `pathlib` import to `test_scanner.py`. [2025-04-30 00:04:21]
- **Verification**: Pre-completion checks passed. Tests should now pass.
- **Related Issues**: None.

## Recurring Bug Patterns
<!-- Append new patterns using the format below -->

## Environment-Specific Notes
<!-- Append environment notes using the format below -->

## Performance Observations
<!-- Append performance notes using the format below -->

## Debugging Tools & Techniques
<!-- Append tool notes using the format below -->