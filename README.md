# Storage Hygiene System

## Overview

The Storage Hygiene System is a command-line tool designed to help users manage and clean up their digital storage. It scans specified directories, analyzes files based on configurable rules (identifying duplicates, large files, old files, etc.), and allows users to review and execute actions like moving files to a staging area for further inspection or deletion.

The system is built with modularity in mind, allowing for potential future extensions like cloud storage integration or more advanced analysis capabilities.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd storage-hygeine
    ```
    *(Replace `<repository-url>` with the actual URL)*

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv .venv
    # On Windows (cmd.exe)
    .\.venv\Scripts\activate.bat
    # On Windows (PowerShell)
    .\.venv\Scripts\Activate.ps1
    # On macOS/Linux
    source .venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Basic Usage

The main entry point for the system is `src/storage_hygiene/main.py`. It accepts several command-line arguments to control its behavior:

```bash
python src/storage_hygiene/main.py [--config CONFIG_PATH] [--targets TARGET_PATHS [TARGET_PATHS ...]] [--db-path DB_PATH] [--dry-run]
```

**Arguments:**

*   `--config CONFIG_PATH` (Optional): Path to the configuration file (`config.yaml`). If not provided, it defaults to `./config.yaml`.
*   `--targets TARGET_PATHS [TARGET_PATHS ...]` (Optional): One or more specific directory paths to scan. If provided, these override the `scan_paths` defined in the configuration file.
*   `--db-path DB_PATH` (Optional): Path to the metadata database file. If provided, this overrides the `database_path` defined in the configuration file. Defaults to `./metadata.db`.
*   `--dry-run` (Optional): If this flag is present, the system will perform the scan and analysis, reporting the actions it *would* take, but will not actually move or modify any files. This is useful for previewing changes.

**Examples:**

*   **Run with default configuration:**
    ```bash
    python src/storage_hygiene/main.py
    ```

*   **Run with a specific configuration file:**
    ```bash
    python src/storage_hygiene/main.py --config /path/to/your/custom_config.yaml
    ```

*   **Scan specific target directories, overriding config:**
    ```bash
    python src/storage_hygiene/main.py --targets /mnt/data/photos /home/user/documents
    ```

*   **Perform a dry run:**
    ```bash
    python src/storage_hygiene/main.py --dry-run
    ```

*   **Use a specific database path and target:**
    ```bash
    python src/storage_hygiene/main.py --db-path /tmp/hygiene.db --targets /mnt/archive --config conf/archive_rules.yaml
    ```

## Core Workflow

The system follows these main steps:

1.  **Configuration Loading:** Reads settings from `config.yaml` (or the path specified by `--config`).
2.  **Scanning:** Traverses the directories specified in `scan_paths` (or by `--targets`). For each file, it collects metadata (path, size, modification time, hash) and stores it in the metadata database (`metadata.db` or path from `--db-path`). Incremental scans are performed based on modification times to improve performance on subsequent runs.
3.  **Analysis:** Queries the metadata database based on the rules defined in the configuration file (e.g., find files larger than X MB, older than Y days, or with duplicate hashes).
4.  **Action Execution / Reporting:** Based on the analysis results and the configured `action` for each rule (e.g., `stage_duplicate`, `review_large`), the system either:
    *   **Dry Run:** Reports the actions that would be taken.
    *   **Normal Run:** Executes the actions, typically moving identified files to a structured `staging_path` defined in the configuration. The database is updated to reflect the new location of moved files.

## Staging Area

The `staging_path` defined in `config.yaml` is a crucial directory where files identified by the analysis rules are moved for user review (unless `--dry-run` is used). The system automatically creates subdirectories within the staging path based on the rule that triggered the move.

For example:

*   Files identified as duplicates might be moved to `<staging_path>/duplicates/`.
*   Files identified as large might be moved to `<staging_path>/large_files/`.
*   Files identified as old might be moved to `<staging_path>/old_files/`.

This structure helps organize the staged files, allowing users to easily review specific categories before deciding on final deletion or archiving. **Files in the staging area are not automatically deleted.** Manual user action is required after review.