# Configuration (`config.yaml`)

The behavior of the Storage Hygiene System is controlled by a configuration file, typically named `config.yaml`. The path to this file can be specified using the `--config` command-line argument; otherwise, it defaults to `./config.yaml`.

## Top-Level Keys

The configuration file uses the following top-level keys:

*   `scan_paths`: A list of directory paths that the system should scan. These paths are scanned recursively. This can be overridden by the `--targets` CLI argument.
*   `staging_path`: The directory where files identified by analysis rules will be moved for review (unless `--dry-run` is used). Subdirectories are created within this path based on the rule type (e.g., `duplicates`, `large_files`).
*   `database_path`: The file path for the metadata database (DuckDB). This can be overridden by the `--db-path` CLI argument.
*   `rules`: A dictionary containing the specific analysis rules to apply.

## Rules Configuration

The `rules` section defines the criteria for identifying files during the analysis phase. Each key under `rules` represents a specific rule type.

### Common Rule Parameters

Most rules share these common parameters:

*   `enabled`: (boolean) Set to `true` to enable the rule, `false` to disable it.
*   `action`: (string) Specifies the action to take when a file matches the rule. Common actions include:
    *   `stage_duplicate`: Move duplicate files to the staging area.
    *   `review_large`: Move large files to the staging area.
    *   `review_old`: Move old files to the staging area.
    *   *(Future actions like `delete` or `archive` might be added)*

### Rule Types

#### 1. `duplicates`

Identifies files with identical content hashes.

*   **Parameters:**
    *   `enabled`: (boolean)
    *   `action`: (string, typically `stage_duplicate`)

*   **Example:**
    ```yaml
    rules:
      duplicates:
        enabled: true
        action: stage_duplicate
    ```

#### 2. `large_files`

Identifies files exceeding a specified size threshold.

*   **Parameters:**
    *   `enabled`: (boolean)
    *   `min_size_mb`: (integer) The minimum file size in megabytes (MB) to trigger the rule.
    *   `action`: (string, typically `review_large`)

*   **Example:**
    ```yaml
    rules:
      large_files:
        enabled: true
        min_size_mb: 1024 # Identify files larger than 1 GB
        action: review_large
    ```

#### 3. `old_files`

Identifies files that haven't been accessed or modified within a specified number of days.

*   **Parameters:**
    *   `enabled`: (boolean)
    *   `min_days_unaccessed`: (integer) The minimum number of days since the last access/modification to trigger the rule.
    *   `action`: (string, typically `review_old`)

*   **Example:**
    ```yaml
    rules:
      old_files:
        enabled: true
        min_days_unaccessed: 365 # Identify files untouched for at least a year
        action: review_old
    ```

## Example `config.yaml`

```yaml
# Paths to scan recursively
scan_paths:
  - /home/user/Documents
  - /mnt/data/media

# Directory to move files for review
staging_path: /home/user/storage_hygiene_staging

# Path for the metadata database
database_path: ./metadata.db

# Analysis rules
rules:
  duplicates:
    enabled: true
    action: stage_duplicate

  large_files:
    enabled: true
    min_size_mb: 500 # Flag files over 500 MB
    action: review_large

  old_files:
    enabled: false # Disabled for now
    min_days_unaccessed: 730 # 2 years
    action: review_old

# Optional: Add future rule types here
# e.g., specific_file_types, empty_folders etc.