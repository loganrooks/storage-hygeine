# Product Context
<!-- Entries below should be added reverse chronologically (newest first) -->
### [2025-04-30 01:33:00] Core System Documentation (User Facing)
- **Summary:** Initial user documentation created covering system overview, installation, CLI usage, configuration (`config.yaml`), core workflow, staging area, and component architecture overview.
- **Links:**
    - [README.md](../../README.md)
    - [Configuration Guide](../../docs/configuration.md)
    - [Architecture Overview](../../docs/architecture_overview.md)

# System Patterns
<!-- Entries below should be added reverse chronologically (newest first) -->
### [2025-04-30 00:14:56] Anti-Pattern: Path Normalization Mismatch
- **Description:** `MetadataStore.update_file_path` failed to find records because the `old_path` string provided by `ActionExecutor` (derived from `str(Path(action_details['path']))`) did not exactly match the primary key stored by `Scanner` (derived from `str(item_path.resolve())`).
- **Cause:** Potential subtle differences in path representation (case, slashes) between scanning and action execution phases, especially on Windows.
- **Resolution:** Applied `os.path.normcase()` to path strings before storing them in `Scanner` and before using them in the `WHERE` clause of `update_file_path` in `ActionExecutor`.
- **Related:** [See Issue: Pytest-Failures-Remaining-13 in debug.md]

### [2025-04-30 00:14:56] Anti-Pattern: Swallowed Critical Exceptions
- **Description:** `ActionExecutor.execute_actions` caught `Exception` within its loop, preventing critical errors like `OSError` (e.g., from invalid staging path) from propagating up to `main.py` and causing a non-zero exit code.
- **Cause:** Overly broad exception handling within the action loop.
- **Resolution:** Modified the `except` block in `ActionExecutor.execute_actions` to specifically catch and re-raise `OSError`, while still catching and logging other `Exception` types non-critically.
- **Related:** [See Issue: Pytest-Failures-Remaining-13 in debug.md]
### Dependency Map (Current - Overwrite this section) - 2025-04-30 00:05:40
```mermaid
graph TD
    subgraph Core Workflow
        CLI --> MainPy[main.py];
        MainPy --> ConfigManager[ConfigManager];
        MainPy --> MetadataStore[MetadataStore];
        MainPy --> Scanner[Scanner];
        MainPy --> AnalysisEngine[AnalysisEngine];
        MainPy --> ActionExecutor[ActionExecutor];
        Scanner --> ConfigManager;
        Scanner --> MetadataStore;
        AnalysisEngine --> ConfigManager;
        AnalysisEngine --> MetadataStore;
        ActionExecutor --> ConfigManager;
        ActionExecutor --> MetadataStore; # Added dependency
    end
```

### [2025-04-30 00:05:40] Anti-Pattern: Interface Mismatch (List vs Dict)
- **Description:** `ActionExecutor.execute_actions` expected a dictionary (`dict[str, list[dict]]`) but was called with a list (`list[dict]`) in unit tests, causing `AttributeError`.
- **Cause:** Discrepancy between component implementation and test setup during TDD/integration.
- **Resolution:** Corrected test calls in `tests/test_action_executor.py` to pass data in the expected dictionary format.
- **Related:** [See Issue: Pytest-Failures-20250430 in debug.md]

### [2025-04-29 18:51:04] Initial Architecture: Storage Hygiene System
- **Description:** A modular system for scanning, analyzing, reviewing, and acting upon files across local and cloud storage. Components include Scanner, Analysis Engine, UI, Executor, Config Manager, and optional AI Assistant.
- **Diagram:** [See Architect Specific Memory Diagram: Storage Hygiene System - 2025-04-29 18:51:04]
- **Key Patterns:** Service-based architecture, separation of concerns (scanning, analysis, action), configuration-driven rules, secure credential management (OS Keychain), scalable metadata storage (DuckDB), parallel processing, incremental scanning, detailed analysis categories (including similarity).
<!-- Entries below should be added reverse chronologically (newest first) -->

### [2025-04-29 19:46:07] System Pattern Refinement: Storage Hygiene System (CLI Focused)
- **Description:** Revised architecture focusing on a CLI-only interface, generalized migration rules, and enhanced detail. Incorporates detailed analysis categories, DuckDB for metadata, OS Keychain for secrets, parallel/incremental scanning, and content-based similarity checks. Addresses scalability, security, cross-platform requirements, modularity, and SPARC/TDD principles more explicitly.
- **Diagram:** [See Architect Specific Memory Diagram: Storage Hygiene System (CLI Detailed) - 2025-04-29 19:46:07]
- **Related Decisions:** [See Decision Log entries for 2025-04-29 19:34:11 and 2025-04-29 19:46:07]

### [2025-04-29 18:51:19] Architectural Approach: Modular Services
### [2025-04-30 00:05:55] Decision: Add MetadataStore Path Update Logic
- **Decision:** Added `update_file_path` method to `MetadataStore` and integrated its call into `ActionExecutor._stage_file` after successful file moves.
- **Rationale:** To ensure the database record accurately reflects the new file location after staging actions (duplicates, large, old files), fixing the `test_main_workflow_non_dry_run` failure where the DB path was not updated. `upsert_file_record` was unsuitable as it relies on the original path as the primary key.
- **Alternatives Considered:** Deleting and re-inserting the record (less efficient, potential data loss if re-insert fails).
- **Related Components:** MetadataStore, ActionExecutor.
- **Related:** [See Issue: Pytest-Failures-20250430 in debug.md]
- **Decision:** Adopt a modular, service-based architecture for the Storage Hygiene System.
- **Rationale:** Enhances maintainability, testability, and allows for independent development/scaling of components (Scanner, Analyzer, UI, Executor). Facilitates potential future replacement or addition of components (like the AI Assistant).
- **Alternatives Considered:** Monolithic script (rejected due to complexity and lack of scalability).
- **Related Patterns:** [See System Pattern: Initial Architecture - 2025-04-29 18:51:04]
# Decision Log
<!-- Entries below should be added reverse chronologically (newest first) -->

### [2025-04-29 20:19:26] Decision: Mandatory Git Commits on Task Success
- **Decision:** Modes modifying project files (code, docs, etc.) must commit project changes AND memory-bank updates in two separate commits upon successful task completion and verification.
- **Rationale:** Ensures version control hygiene, links project state to memory bank state, and provides clear history.
- **Implementation:** SPARC orchestrator will include explicit instructions in `new_task` messages for relevant modes.
### [2025-04-29 19:34:11] Decision: AI Integration Timing
- **Decision:** Implement AI Organization Assistant as a Post-MVP feature.
- **Rationale:** Core functionality (duplicate/large/old file detection, migration) provides significant value independently. Deferring AI complexity allows focus on core stability, performance, and user experience first. Reduces initial development scope and potential costs (API usage).
- **Alternatives Considered:** Integrate AI in V1 (rejected due to complexity and non-core nature).
- **Related Components:** AI Organization Assistant, Analysis Engine.

### [2025-04-29 19:46:07] Decision: Generalized Migration Rules
- **Decision:** Implement a flexible rule engine for defining migration tasks, rather than hardcoding specific source/destination pairs (like OneDrive -> GDrive). Rules will specify source location(s), destination location, and filtering criteria (file types, size, age, patterns, etc.).
- **Rationale:** Provides much greater flexibility for the user to define various migration/backup scenarios between different supported local or cloud locations. Avoids hardcoding specific use cases. Aligns with user feedback requesting generalization.
- **Alternatives Considered:** Hardcoded migration paths (rejected as inflexible).
- **Related Components:** Configuration Manager, Analysis Engine, Action Executor.
- **Reference:** ADR-007

### [2025-04-29 19:46:07] Decision: Cloud/Local Transfer Mechanism (Revised)
- **Decision:** Use direct SDKs (for cloud) or Python file operations (`shutil`, `os`) for transfers (copy/move) between configured sources and destinations, staging via local temporary storage where necessary (e.g., cloud-to-cloud, cloud-to-local). Offer `rclone` integration as an optional alternative backend.
- **Rationale:** Direct SDK/library usage provides maximum control, integration, and feedback. Staging locally handles transfers between locations without direct paths. `rclone` remains a power-user option. This generalizes ADR-005.
- **Alternatives Considered:** Direct cloud-to-cloud (often unavailable/unreliable via standard APIs), Pure `rclone` (external dependency).
- **Related Components:** Action Executor, Configuration Manager.
- **Reference:** ADR-005 (Revised)

### [2025-04-29 19:34:11] Decision: Scalability - Incremental Scans
- **Decision:** Implement incremental scans by comparing file modification times and sizes against stored metadata in DuckDB. Provide full rescan option.
- **Rationale:** Avoids costly re-hashing/re-analysis of unchanged files, significantly speeding up subsequent scans on large filesystems. Filesystem event monitoring (`watchdog`) adds significant complexity better suited for continuous monitoring rather than periodic hygiene tasks.
- **Alternatives Considered:** Filesystem event monitoring (rejected due to complexity), Full rescans only (rejected due to performance on large drives).
- **Related Components:** Scanner Service, Metadata Store (DuckDB).

### [2025-04-29 19:34:11] Decision: Scalability - Metadata Storage
- **Decision:** Use DuckDB as the primary metadata store.
- **Rationale:** DuckDB provides a good balance of embedded simplicity (like SQLite) with strong performance for analytical queries (duplicates, metrics) on potentially terabyte-scale metadata, and handles larger-than-memory datasets effectively.
- **Alternatives Considered:** SQLite (potential write bottlenecks/locking with parallel scanning), File-based (Parquet/CSV - complex updates/transactions), Full RDBMS (overkill for single-user desktop tool).
- **Related Components:** Scanner Service, Analysis Engine, Staging & Review UI, Action Executor.

### [2025-04-29 19:34:11] Decision: Security - Credential Management
- **Decision:** Use the OS Keychain via the Python `keyring` library for storing sensitive credentials (Cloud API keys, Vertex AI key).
- **Rationale:** Offers the best balance of security (OS-level protection) and usability across Windows, macOS, and Linux. Avoids insecure plain text storage or complex custom encryption.
- **Alternatives Considered:** Environment variables (insecure on desktop), Cloud Secrets Manager (overkill), Encrypted file (key management issue).
- **Related Components:** Configuration Manager, Scanner Service, Action Executor, AI Organization Assistant.

### [2025-04-29 19:46:07] Decision: UI Approach (Revised)
- **Decision:** Implement the user interface as **CLI-only**. File review will be handled by outputting lists/reports and allowing users to open specific files in external editors (e.g., Vim, VS Code) based on paths provided by the CLI.
- **Rationale:** Aligns with user preference for simplicity and avoids the complexity of developing/maintaining a separate Web UI or Desktop App. Leverages user familiarity with existing tools for file inspection. Focuses development effort on core backend functionality.
### [2025-04-30 01:33:20] - DocsWriter: Core System Documentation
- **Status:** Completed
- **Details:** Created initial user-facing documentation for the core Storage Hygiene system, including README, configuration guide, and architecture overview.
- **Files:** `README.md`, `docs/configuration.md`, `docs/architecture_overview.md`
- **Related:** Task: Create user-facing documentation [2025-04-30 01:28:23]
- **Alternatives Considered:** Web App UI (rejected based on user feedback), Desktop App (rejected due to complexity).
- **Related Components:** CLI Interface (replaces Staging & Review UI), Core Engine components.
- **Reference:** ADR-001 (Revised)

# Progress
<!-- Entries below should be added reverse chronologically (newest first) -->
### [2025-04-30 02:14:08] - HolisticReview: Workspace Review Completed
- **Status:** Completed
- **Details:** Performed review covering code, tests, docs, config, organization, cohesion, SPARC/TDD adherence, and future readiness. Key findings include major inconsistencies between implemented CLI arguments/Scanner architecture and documentation/plans, minor code hygiene issues, and missing default config. Recommendations focus on alignment and hygiene before proceeding with Phase 2 features.
- **Files:** `docs/reviews/holistic_review_20250430.md`, `memory-bank/mode-specific/holistic-reviewer.md`
- **Related:** Task: Perform comprehensive review [2025-04-30 02:01:55]
### [2025-04-30 00:26:41] - Debug: Remaining Pytest Failures Resolved
- **Status:** Completed
- **Details:** Investigated and fixed the final 10 pytest failures reported after the previous debug session. Issues involved integration test logic (staging paths, invalid YAML handling), unit test assertions (hash key), and error propagation in main.py. All 39 tests now pass.
- **Files:** `src/storage_hygiene/scanner.py`, `src/storage_hygiene/main.py`, `tests/integration/test_main_workflow.py`, `tests/test_analysis_engine.py`, `tests/test_scanner.py`
- **Related:** [See Issue: Pytest-Failures-Remaining-10 in debug.md]
### [2025-04-30 00:05:25] - Debug: Pytest Failures Resolved
- **Status:** Completed
- **Details:** Investigated and fixed 16 pytest failures reported after initial integration. Issues involved interface mismatches (ActionExecutor), import errors (AnalysisEngine), missing logic (MetadataStore path update), incorrect error handling (main.py exit codes), and incorrect test assertions (Scanner mocks, Main workflow paths/logs).
- **Files:** `src/storage_hygiene/action_executor.py`, `src/storage_hygiene/analysis_engine.py`, `src/storage_hygiene/metadata_store.py`, `src/storage_hygiene/main.py`, `tests/test_action_executor.py`, `tests/test_analysis_engine.py`, `tests/test_scanner.py`, `tests/integration/test_main_workflow.py`
- **Related:** [See Issue: Pytest-Failures-20250430 in debug.md]
### [2025-04-29 23:45:11] - Integration: Core Component Workflow
- **Status:** Completed & Tested (Dry Run)
- **Details:** Created `main.py` script to orchestrate `ConfigManager`, `MetadataStore`, `Scanner`, `AnalysisEngine`, `ActionExecutor`. Added CLI argument parsing (`argparse`). Updated `__init__.py`. Created and passed integration test `test_main_workflow_dry_run`. Fixed multiple interface mismatches identified during testing.
- **Files:** `src/storage_hygiene/main.py`, `src/storage_hygiene/__init__.py`, `tests/integration/test_main_workflow.py`
- **Related:** Integration Point: Main Script Orchestration - 2025-04-29 23:45:11