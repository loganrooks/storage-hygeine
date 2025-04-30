# Storage Hygiene System - Detailed Architecture Report

**Version:** 2.0
**Date:** 2025-04-29
**Status:** Proposed (Revised based on feedback)

## 1. Overview

This document outlines the proposed architecture for the Storage Hygiene System, a **CLI-first tool** designed to assist users in managing local and cloud storage. The system scans specified locations, analyzes file metadata to identify potential candidates for deletion or organization based on various criteria (duplicates, similarity, age, size, type, corruption, etc.), presents findings via CLI reports, allows user confirmation, executes actions (delete, move, transfer), and supports configurable data migration/backup rules.

This revision incorporates user feedback, focusing on a CLI-only interface, increased detail, explicit discussion of modularity and development principles (SPARC/TDD), generalized transfer rules, and a phased development plan.

## 2. Goals & Requirements (Revised)

*   **Primary Interface:** Command Line Interface (CLI) for all operations (scan, analyze, report, configure, confirm, execute).
*   **Scanning:** Traverse user-configured locations: local drives/folders, external drives, cloud storage (OneDrive, Google Drive initially). Handle large volumes (TBs) efficiently.
*   **Metadata Storage:** Persist comprehensive file metadata (path, size, dates, hashes, flags) in a local, efficient database (DuckDB). Support incremental scans.
*   **Analysis Categories:** Identify files based on configurable rules:
    *   **Exact Duplicates:** SHA-256 hash comparison.
    *   **Similar Content:** Configurable methods and thresholds:
        *   Perceptual hash (pHash/aHash via `imagehash`) for images/videos.
        *   Fuzzy hash (`ssdeep`) for documents/text.
        *   Acoustic fingerprint (`pyacoustid`/`fpcalc`) for audio.
        *   **Configurable Prioritization:** Rules within similarity groups (based on resolution, size, filename keywords, date, corruption status) to identify best version(s) to keep.
    *   **File Attributes:** Size thresholds, age thresholds (modified/accessed).
    *   **File Types/Patterns:** Temporary files, cache files, log files, build files, zero-byte files, empty folders.
    *   **Potential Corruption (Multi-Level & Configurable):**
        *   Level 1 (Default): Header/magic number (`python-magic`), basic archive (`zipfile`), basic PDF (`PyPDF2`). Flags: `corrupt_header`, `corrupt_structure_basic`.
        *   Level 2 (Optional): Full structure validation (e.g., read all PDF pages). Flags: `corrupt_structure_full`.
        *   Level 3 (Optional, Requires `ffmpeg`): Media content sampling. Attempts to decode small samples from the **start, middle, and end** of media files using `ffmpeg`. Flags: `corrupt_content_sample`.
        *   **Configurable Actions:** Different actions can be configured based on specific corruption flags (e.g., ignore `corrupt_content_sample` unless `corrupt_header` is also present).
    *   **Location Specific:** Recycle Bin/Trash contents.
    *   **Disorganization Metrics:** Root file ratio, folder depth, generic names, etc.
*   **Reporting:** Generate clear CLI reports (tables, file lists) filterable by analysis category or other criteria. Output reports to console or files (txt, CSV, JSON).
*   **Review & Confirmation:** Allow users to review report files using external tools (editors, viewers). Provide safe CLI mechanisms (interactive prompts, explicit flags) for confirming actions on specific files or categories.
*   **Action Execution:** Reliably execute confirmed actions:
    *   Delete (Move to OS Trash via `send2trash`, or permanent delete).
    *   Move/Copy (Local filesystem operations via `shutil`).
    *   Transfer (Move/Copy between configured local/cloud locations via SDKs/`shutil`, using local staging for indirect paths like cloud-to-cloud).
*   **Generalized Transfer Rules:** Allow users to define flexible rules in configuration for copy/move actions based on source, destination, and filters (ADR-007).
*   **Security:** Securely manage cloud API credentials using OS Keychain (`keyring`), avoiding hardcoding or plain text storage (ADR-002).
*   **Performance & Scalability:** Handle large filesystems via parallel scanning (`multiprocessing`), incremental updates (ADR-004), efficient database queries (DuckDB - ADR-003), and API batching/retries.
*   **Cross-Platform:** Core functionality must run on Windows and Linux.
*   **Modularity & Maintainability:** Design components with clear responsibilities and interfaces. Follow SPARC/TDD principles.
*   **(Post-MVP):** AI-driven organization suggestions (ADR-006).

## 3. High-Level Architecture (CLI-Focused)

The system employs a modular architecture centered around a CLI interface orchestrating backend components that interact via a central DuckDB metadata store and a YAML-based configuration system. Parallelism is used for scanning, and potentially for intensive analysis tasks.

```mermaid
graph LR
    subgraph User Interaction
        direction TB
        CLI[CLI Interface (click/typer)];
        CLI -- Manages --> Config;
        CLI -- Triggers --> ScanPool;
        CLI -- Triggers --> Analysis;
        CLI -- Triggers --> Executor;
        CLI -- Displays Reports/Progress --> User((User));
        User -- Provides Input/Commands --> CLI;
        User -- Reviews Files --> ExternalTools[External Editors/Viewers];
        CLI -- Provides File Paths --> ExternalTools;
    end

    subgraph Configuration
        direction TB
        Config[Configuration Manager] -- Reads --> ConfigFiles(YAML - Rules, Paths);
        Config -- Get/Set Credentials --> OSKeychain[(OS Keychain via 'keyring')];
    end

    subgraph Core Engine
        direction TB
        ScanPool[Scanner Pool (multiprocessing)];
        ScanPool -- Writes Metadata Queue --> DBWriter[DB Writer Process];
        DBWriter -- Writes/Updates --> MetaDB[(DuckDB Metadata Store)];
        Analysis[Analysis Engine] -- Reads/Updates --> MetaDB;
        Executor[Action Executor] -- Reads Actions / Updates Status --> MetaDB;
    end

    subgraph Data Sources & Targets
        direction TB
        FS[Local/External Filesystem];
        OneDriveAPI[MS Graph API];
        GDriveAPI[Google Drive API];
        VertexAIAPI[Vertex AI API (Post-MVP)];
        Trash[OS Trash (send2trash)];
    end

    subgraph Optional AI (Post-MVP)
        direction TB
        AIAssist[AI Organization Assistant];
        AIAssist -- Gets Key --> Config;
        AIAssist -- Calls --> VertexAIAPI;
        Analysis -- Sends Metadata Summary --> AIAssist;
        AIAssist -- Returns Suggestions --> Analysis; %% Suggestions stored in DB
    end

    %% Connections
    Config -- Provides Config --> ScanPool;
    Config -- Provides Config --> Analysis;
    Config -- Provides Config --> Executor;
    Config -- Provides Config --> AIAssist;

    ScanPool -- Scans --> FS;
    ScanPool -- Scans --> OneDriveAPI;
    ScanPool -- Scans --> GDriveAPI;
    ScanPool -- Gets Credentials --> Config;

    Analysis -- Uses Rules From --> Config;
    Analysis -- Gets Credentials (for AI) --> Config;

    Executor -- Acts On --> FS;
    Executor -- Acts On --> Trash;
    Executor -- Acts On --> OneDriveAPI;
    Executor -- Acts On --> GDriveAPI;
    Executor -- Gets Credentials --> Config;
    Executor -- Uses Rules From --> Config;

    %% Style
    classDef db fill:#f9f,stroke:#333,stroke-width:2px;
    classDef api fill:#ccf,stroke:#333,stroke-width:2px;
    classDef secure fill:#f96,stroke:#333,stroke-width:2px;
    class MetaDB,OSKeychain,OneDriveAPI,GDriveAPI,VertexAIAPI db;
    class OSKeychain secure;
```
**Diagram Notes:** CLI-focused architecture. Parallel scanning feeds a dedicated DB writer. Analysis and Execution interact primarily with DuckDB based on configuration rules. Credentials use OS Keychain. AI is optional.

## 4. Core Components (Detailed)

*(Component details expanded based on feedback and revised design)*

### 4.1. CLI Interface
- **Responsibility**: Primary user interaction point. Parses commands/args (`scan`, `analyze`, `report`, `confirm`, `execute`, `config`). Orchestrates backend calls. Displays formatted reports (`rich`), progress (`tqdm`/`rich`), logs. Handles interactive confirmation (`inquirerpy`).
- **Key Logic/Algorithms**: Command parsing tree (using `click` or `typer`). Argument validation. Mapping commands to backend service calls. Formatting DuckDB query results into tables/lists. Progress bar updates based on backend feedback (e.g., items processed). Interactive confirmation loops. Safe handling of destructive action confirmation (e.g., require `--force` or specific confirmation text).
- **Dependencies**: `click`/`typer`, `rich`, `tqdm`/`rich.progress`, `inquirerpy`, Backend Components (`Configuration Manager`, `Scanner Service`, `Analysis Engine`, `Action Executor`), `Metadata Store` (for reporting queries).
- **Interfaces**: Exposes CLI commands. Consumes Python APIs of backend components. Reads/Writes Stdout/Stderr.
- **Error Handling**: Catches specific exceptions from backend (e.g., `ConfigValidationError`, `ScanError`, `AnalysisError`, `ExecutionError`), presents user-friendly messages using `rich`. Handles CLI argument errors. Uses non-zero exit codes on failure.
- **SPARC/TDD**: TDD for command parsing (`click.testing.CliRunner`), argument validation, output formatting (asserting stdout/stderr). Mock backend components to test orchestration logic. Integration tests for end-to-end command flows.

### 4.2. Scanner Service (Pool)
- **Responsibility**: Efficiently traverse configured locations (local/cloud). Gather metadata (`stat`, SDK calls). Calculate SHA-256 (`hashlib`). Perform incremental checks (DB query `mtime`/`size`). Put results on DB Writer queue.
- **Key Logic/Algorithms**: Uses `multiprocessing.Pool` and `multiprocessing.Queue`. Distributes directories/cloud prefixes via `pool.imap_unordered`. Worker process logic:
    1. Receive path/prefix.
    2. Use `os.scandir` (preferred for performance) or `os.walk` for local traversal, `pathlib.Path.stat` for metadata.
    3. Use cloud SDK list/get methods (handle pagination) for cloud traversal/metadata.
    4. Query DuckDB (read-only connection or via message to main process) for existing path record.
    5. Compare `mtime`/`size`. If changed/new:
        a. Read file content in chunks (`io.BytesIO.read(chunk_size)`).
        b. Update `hashlib.sha256` with each chunk.
        c. Get final hash digest.
    6. Construct `FileMetadata` dictionary.
    7. Put dict onto the output queue.
- **Dependencies**: `multiprocessing`, `pathlib`, `os`, `hashlib`, `io`, `Configuration Manager`, `Metadata Store` (read access), Cloud SDKs (`msgraph-sdk`, `google-api-python-client`), `DB Writer Process Queue`, `tenacity` (for cloud retries).
- **Interfaces**: Accepts config. Internal: Puts dicts on `Queue`.
- **Error Handling**: Log skips with reasons (permissions `PermissionError`, not found `FileNotFoundError`, cloud API errors `ApiException`). Use `tenacity` for retrying transient cloud errors (429, 5xx). Handle cloud authentication errors early via Config Manager check.
- **SPARC/TDD**: TDD for `stat` parsing, chunked hashing, incremental DB check logic, cloud metadata extraction. Mock `os.scandir`, `pathlib.Path`, SDK clients, DB connection. Use `pyfakefs` for local filesystem testing. Integration tests with small local dirs/mock cloud endpoints.

### 4.3. DB Writer Process
- **Responsibility**: Dedicated process consuming `FileMetadata` dicts from queue. Performs batch upserts into DuckDB `FileMetadata` table.
- **Key Logic/Algorithms**: Loop reading from queue until sentinel value received. Accumulate items into a batch (e.g., list of tuples/dicts). Periodically (e.g., every N items or T seconds) execute batch `INSERT INTO FileMetadata (...) VALUES (...), (...) ON CONFLICT (full_path) DO UPDATE SET ...` statement. Manage single DuckDB write connection lifecycle.
- **Dependencies**: `multiprocessing` (Queue), `duckdb`.
- **Interfaces**: Internal: Consumes from `Queue`. Interacts with DuckDB file.
- **Error Handling**: Catch `duckdb.Error` during connection/write. Log error. Strategy for failed batches (e.g., log failed items, potentially retry individual items - complex). Graceful shutdown on sentinel value or error.
- **SPARC/TDD**: Infrastructure. Test queue consumption and batch insertion logic. Verify DB state after processing known queue inputs. Mock `duckdb.connect` and queue methods.

### 4.4. Analysis Engine
- **Responsibility**: Apply analysis rules. Perform similarity/corruption checks (multi-level). Calculate metrics. Match transfer rules. Update `FileMetadata` flags. Generate `ActionItem` records (`status='PENDING_CONFIRMATION'`).
- **Key Logic/Algorithms**:
    *   **Duplicates:** As before (Group by `sha256_hash`).
    *   **Size/Age/Type Rules:** As before (SQL `UPDATE` based on attributes/patterns).
    *   **Similarity:** As before (Dispatch hash calculation to pool, group results, update DB with `similarity_hash` and `similarity_group_id`). **Add configurable threshold comparison** when grouping. **Add prioritization logic:** After grouping, query group members, apply configured prioritization rules (resolution, size, keywords, date, corruption flags) using SQL `CASE` statements or Python logic, and update flags like `similar_low_priority` on non-preferred items.
    *   **Corruption (Multi-Level):**
        *   Level 1 (Header/Basic Structure): Fetch candidates, dispatch checks (`python-magic`, `zipfile.testzip`, basic `PyPDF2` read) to pool. Update flags (`corrupt_header`, `corrupt_structure_basic`).
        *   Level 2 (Full Structure - Optional): If enabled, dispatch deeper checks (e.g., read all PDF pages) to pool. Update flag (`corrupt_structure_full`).
        *   Level 3 (Media Sampling - Optional): If enabled, dispatch `ffmpeg` sampling command (e.g., attempting to decode 1 frame each at 0%, 50%, 95% positions via `subprocess`) to pool. Check exit code/stderr. Update flag (`corrupt_content_sample`).
    *   **Metrics:** As before (SQL queries).
    *   **Transfer Rule Matching:** As before (Iterate rules, construct SQL `WHERE`, `INSERT` into `ActionItem`). Ensure `WHERE` clause can use new flags like `similar_low_priority` and specific corruption flags (`has_flag:corrupt_header`, `not_has_flag:corrupt_content_sample`).
- **Dependencies**: `Metadata Store` (DuckDB R/W), `Configuration Manager`, `concurrent.futures.ProcessPoolExecutor`, Analysis Libraries (`imagehash`, `ssdeep`, `pyacoustid`+`fpcalc`, `python-magic`, `zipfile`, `PyPDF2`), `pydantic`/`jsonschema`, `subprocess` (for `ffmpeg`).
- **Interfaces**: Triggered by CLI. Reads/Writes DuckDB.
- **Error Handling**: Catch analysis library exceptions, `subprocess.CalledProcessError` from `ffmpeg`. Handle DB errors. Log issues. Mark files with analysis errors.
- **SPARC/TDD**: TDD for similarity prioritization logic, multi-level corruption checks (mocking libraries/`subprocess`), and transfer rule matching with new flags.

### 4.5. Action Executor
- **Responsibility**: Read `CONFIRMED` `ActionItem` records. Execute actions (delete, trash, copy/move local/cloud). Use local staging. Implement retries. Update `ActionItem` status/message.
- **Key Logic/Algorithms**: Fetch confirmed actions query (see Interfaces). Loop through items. Dispatch to handler based on `action_type` and source/destination type (local, cloud provider X, trash).
    *   `MOVE_TRASH`: `send2trash.send2trash(source_path)`.
    *   `DELETE`: `os.remove(source_path)` or `os.rmdir(source_path)`.
    *   `MOVE_LOCAL`: `shutil.move(source_path, target_path)`.
    *   `COPY_LOCAL`: `shutil.copy2(source_path, target_path)` (preserves metadata).
    *   `COPY/MOVE_CLOUD`: Use SDK methods (e.g., `download_file`, `upload_file`, `delete_item`). Wrap calls with `@tenacity.retry` decorator for transient errors. Use `tempfile.TemporaryDirectory` for staging cloud-to-cloud or cloud-to-local. Check disk space before download. Handle conflicts based on rule options. Delete source for `MOVE_CLOUD` only after successful upload.
- **Dependencies**: `Metadata Store` (DuckDB R/W), `Configuration Manager`, `send2trash`, `shutil`, `os`, `pathlib`, `tempfile`, Cloud SDKs, `tenacity`. Optional: `subprocess`.
- **Interfaces**: Triggered by CLI. Reads/Writes DuckDB. Interacts with FS/Cloud APIs/Trash.
- **Error Handling**: Catch specific exceptions (`FileNotFoundError`, `PermissionError`, `OSError` [check `errno`], `send2trash.TrashPermissionError`, SDK exceptions, API errors). Log detailed error in `ActionItem.result_message`. Update status to `FAILED`. Implement conflict resolution.
- **SPARC/TDD**: TDD for each action handler (mocking FS/SDKs/DB/`send2trash`). Use `pyfakefs`. Test retry logic with mock exceptions. Test conflict handling. Integration tests with mock APIs.

### 4.6. Configuration Manager
- **Responsibility**: Load/Save/Validate config (YAML). Securely manage credentials (OS Keychain). Provide config/credentials. Support CLI updates.
- **Key Logic/Algorithms**: Use `appdirs.user_config_dir` / `user_data_dir` for default paths. Load YAML (`PyYAML`). Validate using `pydantic` models representing config structure (rules, paths, thresholds). Use `keyring.get_password`/`set_password`. Prompt for missing credentials via CLI. Save non-sensitive parts back to YAML.
- **Dependencies**: `PyYAML`, `keyring`, `pydantic`, `pathlib`, `appdirs`.
- **Interfaces**: Python API (`get_rule`, `get_credential`), CLI (`hygiene config`).
- **Error Handling**: Handle `FileNotFoundError` (create default config), `yaml.YAMLError`, `pydantic.ValidationError`, `keyring` errors. Clear CLI messages.
- **SPARC/TDD**: TDD for load/save/validation/credential logic. Mock `keyring`, filesystem (`pyfakefs`), `appdirs`. Test default config creation.

### 4.7. Metadata Store (DuckDB)
- **Responsibility**: Persist `FileMetadata`, `ActionItem`. Provide efficient SQL querying.
- **Dependencies**: `duckdb`.
- **Interfaces**: SQL via `duckdb` connections.
- **Internal Structure**: Single DB file (e.g., via `appdirs.user_data_dir`). Schema defined (see Data Models). Indexes.
- **Error Handling**: Handled by clients. Recommend user backups.
- **SPARC/TDD**: Data layer. Test interactions via mocking in client tests.

### 4.8. AI Organization Assistant (Optional, Post-MVP)
- **Responsibility**: Construct prompts from metadata summaries, call Vertex AI, parse suggestions, store in `FileMetadata.ai_suggestion`.
- **Dependencies**: `Analysis Engine`, `Configuration Manager`, `google-cloud-aiplatform`.
- **Interfaces**: Internal Python API.
- **Internal Structure**: Prompt generation, API call (with retries), response parsing.
- **Error Handling**: Handle API/parsing errors. Log issues.
- **SPARC/TDD**: TDD for prompt/parsing. Mock API calls.

## 5. Data Models (Revised SQL)

### 5.1. FileMetadata Table
```sql
CREATE TABLE FileMetadata (
  id BIGINT PRIMARY KEY, -- Consider UUID or hash-based ID for distributed generation? Or simple AUTOINCREMENT?
  scan_session_id VARCHAR, -- Identifier for the scan run (e.g., timestamp or UUID)
  full_path VARCHAR UNIQUE NOT NULL, -- Full absolute path, indexed
  is_directory BOOLEAN NOT NULL,
  size_bytes BIGINT, -- Indexed
  created_time TIMESTAMP,
  modified_time TIMESTAMP, -- Indexed
  accessed_time TIMESTAMP,
  owner VARCHAR,
  permissions VARCHAR, -- e.g., '0o755'
  mime_type VARCHAR, -- Indexed
  sha256_hash VARCHAR, -- Indexed
  similarity_hash VARCHAR, -- e.g., 'phash:abcdef123456', 'fuzzy:...'
  similarity_group_id VARCHAR, -- Indexed
  analysis_flags LIST(VARCHAR), -- DuckDB LIST type, consider index if needed/supported
  disorganization_metric_flags LIST(VARCHAR), -- DuckDB LIST type
  ai_suggestion VARCHAR,
  last_seen TIMESTAMP NOT NULL, -- Indexed
  first_seen TIMESTAMP NOT NULL
);
```

### 5.2. ActionItem Table
```sql
CREATE TABLE ActionItem (
  id BIGINT PRIMARY KEY, -- Or AUTOINCREMENT
  file_id BIGINT NOT NULL REFERENCES FileMetadata(id) ON DELETE CASCADE, -- Indexed
  rule_name VARCHAR, -- Indexed
  action_type VARCHAR NOT NULL, -- e.g., 'DELETE', 'MOVE_TRASH', 'COPY_LOCAL', ...
  target_path VARCHAR,
  status VARCHAR NOT NULL, -- Indexed: 'PENDING_CONFIRMATION', 'CONFIRMED', ...
  result_message VARCHAR,
  suggestion_time TIMESTAMP NOT NULL,
  confirmation_time TIMESTAMP,
  execution_time TIMESTAMP
);
```

## 6. Interface Definitions (Revised for CLI)

### 6.1. Scanner Output Queue Item
- **Format**: Python dictionary matching `FileMetadata` structure.
- **Producer**: Scanner Workers
- **Consumer**: DB Writer Process

### 6.2. CLI Reports
- **Format**: `rich.Table`, plain text lists, CSV, JSON via DuckDB queries.
- **Producer**: CLI Reporting functions
- **Consumer**: Stdout / Files / User

### 6.3. Executor Input Query
- **Format**: SQL `SELECT ai.*, fm.full_path as source_path FROM ActionItem ai JOIN FileMetadata fm ON ai.file_id = fm.id WHERE ai.status = 'CONFIRMED'`. Returns list of dicts.
- **Producer**: Action Executor
- **Consumer**: DuckDB

## 7. Modularity Strategy

*   **Component Separation:** Each core component (CLI, Scanner, Analyzer, Executor, Config, DB Writer, Metadata Store) will reside in its own Python module/package (e.g., `storage_hygiene.cli`, `storage_hygiene.scanner`, etc.).
*   **Interface Definition:**
    *   Interaction between CLI and backend components is via Python function/class APIs within the same process.
    *   Interaction between Scanner workers and DB Writer is via a `multiprocessing.Queue` passing dictionaries.
    *   Interaction between Analyzer/Executor/CLI Reporting and the Metadata Store is via DuckDB SQL queries.
    *   Interaction with external services (Cloud APIs, OS Keychain, Filesystem, Trash) is encapsulated within relevant components (Scanner, Executor, Config).
*   **Dependency Injection (Implicit):** While full DI frameworks might be overkill, components will generally be instantiated and passed necessary dependencies (like Config Manager instance, DB connection/path) during application startup or command execution, rather than using global singletons.
*   **Configuration Driven:** Analysis rules and Transfer rules are defined in external YAML configuration, allowing behavior changes without code modification, enhancing modularity.
*   **Plugin System (Future):** A potential future enhancement is a plugin system (e.g., using `pluggy` or `importlib.metadata entry_points`) allowing third-party extensions for analysis rules, action types, or cloud providers.

## 8. SPARC/TDD Alignment

This project will adhere to SPARC principles and utilize Test-Driven Development (TDD).

*   **SPARC Workflow:**
    *   **Specification (User/Architect):** User provides initial request & feedback. Architect refines requirements, defines high-level components, ADRs (this document).
    *   **Pseudocode (Spec Writer Mode):** For complex algorithms (e.g., similarity clustering, rule matching), Spec Writer mode can generate detailed pseudocode and identify TDD anchors (key test cases).
    *   **Architecture (Architect Mode):** Defines component boundaries, interfaces, data models, technology choices (as done here).
    *   **Refinement (Optimizer Mode):** Can be invoked later to improve performance (e.g., optimize DB queries, parallelization strategies).
    *   **Code (Code Mode):** Implements components based on specs and architecture, following TDD.
    *   **Test (TDD Mode / QA Tester Mode):** TDD mode focuses on unit/integration tests during development. QA Tester mode performs end-to-end testing on integrated features.
    *   **Debug (Debugger Mode):** Troubleshoots issues found during testing or reported by users.
    *   **Integration (System Integrator Mode):** Ensures components work together correctly.
*   **TDD Approach:**
    *   Development will follow the Red-Green-Refactor cycle.
    *   **Unit Tests:** Each component's core logic will be tested in isolation using `pytest`. Dependencies (filesystem, DB, APIs, other components) will be mocked using libraries like `pytest-mock`, `pyfakefs`, and custom test doubles.
        *   *Example (Scanner):* Test `calculate_sha256(file_path)`: Mock `open`, write test asserting correct hash for known input -> implement function -> refactor.
        *   *Example (Analyzer):* Test `find_duplicates(db_conn)`: Mock `db_conn.execute().fetchall()` to return sample hash groups -> write test asserting correct `UPDATE` statement is generated -> implement function -> refactor.
    *   **Integration Tests:** Test interactions between components, still potentially mocking external boundaries (APIs, OS Keychain).
        *   *Example:* Test Scanner Pool -> DB Writer interaction using real `multiprocessing.Queue` and an in-memory DuckDB instance.
        *   *Example:* Test CLI `scan` command using `click.testing.CliRunner` and `pyfakefs`.
    *   **End-to-End Tests (Manual/QA):** Run actual commands against sample local directories and potentially sandboxed cloud accounts (if feasible) to verify overall workflow.

## 9. Dependency Analysis

*   **Core Python Libs:** `pathlib`, `os`, `hashlib`, `multiprocessing`, `concurrent.futures`, `logging`, `tempfile`, `io`, `json`, `csv`. (Standard Library)
*   **CLI:** `click` or `typer` (Choice TBD, both good), `rich`, `tqdm` or `rich.progress`, `inquirerpy`. (Well-maintained, common CLI tools)
*   **Configuration:** `PyYAML`, `pydantic` (for validation), `appdirs`. (Standard choices)
*   **Database:** `duckdb`. (Mature, actively developed, good performance for use case)
*   **Security:** `keyring`. (Standard library for keychain access, relies on OS backend)
*   **Actions:** `send2trash`. (Cross-platform trash implementation)
*   **Cloud SDKs:** `google-api-python-client` & `google-auth-oauthlib` (Google Drive), `msgraph-sdk` (OneDrive). (Official SDKs)
*   **Analysis Libs:**
    *   `python-magic`: (Requires libmagic C library - potential installation hurdle)
    *   `imagehash`: (Pure Python options available, Pillow dependency)
    *   `ssdeep`: (Requires `fuzzyhashlib` wrapper and ssdeep C library - potential installation hurdle)
    *   `pyacoustid`: (Requires `fpcalc` external executable - potential installation hurdle/PATH issue)
    *   `zipfile`, `PyPDF2`: (Standard/Common libraries)
*   **Retries:** `tenacity`. (Robust retry library)
*   **Testing:** `pytest`, `pytest-mock`, `pyfakefs`, `click.testing`.
*   **Potential Conflicts/Issues:** Installation of C libraries (`libmagic`, `libfuzzy`) or external executables (`fpcalc`) might require extra steps for users depending on their OS and environment (e.g., package managers `apt`, `brew`, `choco`, or manual compilation). Documentation must cover this.

## 10. Potential Future Features (Expanded)

*   **More Cloud Providers:** Dropbox (`dropbox` SDK), Box (`boxsdk`), S3/compatible (`boto3`), Azure Blob Storage (`azure-storage-blob`). Requires adding specific client logic to Scanner/Executor.
*   **Plugin System:** Use `pluggy` or `importlib.metadata` entry points for:
    *   Custom Analysis Rules (e.g., project-specific cleanup).
    *   Custom Action Types (e.g., call external script).
    *   Custom Report Formats.
    *   Support for new Cloud Providers/Filesystems.
*   **Undo Functionality:** Implement actions (especially delete) via a robust staging area (dedicated hidden folder). Log actions meticulously. Provide `hygiene undo <action_id>` command. Complex to handle dependencies and partial failures.
*   **Scheduled Scans:** Integrate with OS schedulers (`cron`, Task Scheduler) via helper commands or use a Python scheduling library (`schedule`, `apscheduler`) if running as a persistent service (adds complexity).
*   **Advanced Reporting:** Generate simple HTML reports with links. Export full DB tables to CSV/JSON/Parquet for external analysis. Basic charting of metrics over time.
*   **Filesystem Health:** Integrate `smartmontools` (via subprocess) or platform APIs to report basic disk health.
*   **Advanced Corruption:** Deeper checks for media files (e.g., full decode attempt with `ffmpeg`), database files, etc. Very resource-intensive.
*   **Password Manager Integration:** Use CLI tools (e.g., `op`, `bw`, `keepassxc-cli`) via `subprocess` as an alternative credential source in Config Manager.
*   **Cross-Location Deduplication:** Requires comparing hashes (`sha256_hash`) across different scan roots/providers. Complex analysis query.
*   **TUI Interface:** Optional Textual User Interface using `textual` as a richer alternative/complement to the pure CLI, potentially reusing much of the CLI orchestration logic.

## 11. Development Plan / Roadmap (Phased)

This plan prioritizes core functionality and stability, deferring more complex or optional features.

**Phase 1: Core CLI & Local Analysis/Actions (MVP)**
*   **Goal:** Functional CLI tool for scanning local drives, identifying basic categories, reporting, and executing local actions (trash/delete/move).
*   **Components:** CLI Interface (basic commands), Configuration Manager (YAML load/save, basic rules, Keychain), Scanner Service (local only, SHA256, incremental), DB Writer, Metadata Store (DuckDB schema), Analysis Engine (duplicates, size, age, basic patterns), Action Executor (trash, delete, move local).
*   **Key Features:** `scan`, `analyze` (basic), `report` (basic categories), `config`, `confirm`, `execute` (local actions).
*   **Testing:** Unit tests for all components, integration tests for CLI commands and DB interactions (local).

**Phase 2: Cloud Integration & Advanced Analysis**
*   **Goal:** Add cloud scanning/actions, generalized transfer rules, and advanced analysis types.
*   **Components:** Enhance Scanner (add OneDrive/GDrive support, SDKs, auth flow via Keychain), Enhance Executor (add cloud transfer logic, staging, generalized rule handling), Enhance Analysis Engine (similarity hashing, corruption checks, metrics, transfer rule matching), Enhance Config Manager (transfer rule schema/validation).
*   **Key Features:** Scan cloud locations, advanced analysis reports (similarity, corruption, metrics), execute generalized transfer rules (local-cloud, cloud-local, cloud-cloud).
*   **Testing:** Mock cloud SDKs for unit/integration tests. Manual testing against real (sandboxed) cloud accounts. Test transfer rule logic thoroughly.

**Phase 3: Extensibility & Optional Features**
*   **Goal:** Implement post-MVP features based on priority and feedback.
*   **Components:** AI Organization Assistant (if pursued), Plugin System architecture, Scheduling logic, Advanced Reporting features, Undo mechanism (if feasible).
*   **Key Features:** AI suggestions, support for plugins, scheduled scans, HTML reports, etc.
*   **Testing:** Unit/integration tests for new features. Test plugin loading/execution.

**Cross-Cutting:** Documentation (user guide, config examples, installation), cross-platform testing (Windows, Linux), performance profiling and optimization will occur throughout all phases.