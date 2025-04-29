# ADR-007: Generalized Transfer Rules

**Date:** 2025-04-29
**Status:** Proposed

## Context

The system needs to perform various file actions, including deletion, moving files locally, and transferring files between different locations (local folders, cloud storage providers). The initial request mentioned migrating non-media files from OneDrive to Google Drive, but user feedback indicated a need for a more flexible and general mechanism to define different transfer scenarios.

## Decision

We will implement a **rule-based system for defining transfer actions** within the `Configuration Manager`. Instead of hardcoding specific migration paths, users can define named transfer rules in the configuration file (e.g., YAML). Each rule will specify:
1.  **`name`**: A unique identifier for the rule (e.g., `backup_docs_to_gdrive`, `archive_old_projects`, `move_downloads_to_staging`).
2.  **`action_type`**: The type of transfer (e.g., `COPY`, `MOVE`).
3.  **`source`**: Defines the source location(s). This could be:
    *   A specific local path (`/path/to/docs`).
    *   A specific cloud path (`onedrive:/Documents`, `gdrive:/Backup`).
    *   A category identified by the `Analysis Engine` (e.g., `category:large_files`, `category:old_projects_tag`).
4.  **`destination`**: Defines the target location. This could be:
    *   A specific local path (`/path/to/backup/`).
    *   A specific cloud path (`gdrive:/ArchivedStuff`).
    *   A special target like `TRASH` or `PERMANENT_DELETE`.
5.  **`filters` (Optional)**: Criteria to select specific files from the source. This can include:
    *   File name patterns (`*.log`, `invoice_*.pdf`).
    *   MIME type patterns (`image/*`, `!video/*`).
    *   Size constraints (`>1GB`, `<10MB`).
    *   Date constraints (modified/accessed before/after a date).
    *   Analysis flags (`has_flag:duplicate`, `!has_flag:temp_file`).
6.  **`options` (Optional)**: Rule-specific options like:
    *   `conflict_resolution`: `skip`, `rename`, `overwrite`.
    *   `delete_source_after_transfer`: `true`/`false` (for `MOVE` actions).

The `Analysis Engine` will evaluate these rules against the file metadata. If a file matches a rule's source and filters, the corresponding action (with source, destination, type) will be suggested. The `Action Executor` will then perform the transfer based on the confirmed `ActionItem` referencing the rule (see ADR-005 Revised).

## Rationale

*   **Flexibility & User Control:** Allows users to define custom workflows for backup, migration, archival, or cleanup across different local and cloud locations without requiring code changes.
*   **Extensibility:** New source/destination types (e.g., other cloud providers, SFTP) or filter criteria can be added by extending the rule engine and the `Action Executor`'s capabilities.
*   **Decoupling:** Separates the definition of *what* to transfer (rules in config) from the *how* to transfer (logic in `Action Executor`).
*   **Addresses Feedback:** Directly implements the user's request for a more generalized migration/transfer system instead of a hardcoded OneDrive-to-GDrive feature.

## Alternatives Considered

*   **Hardcoded Transfer Paths/Logic:** Rejected as inflexible and not meeting user requirements for generalization.
*   **Scripting Language Integration (e.g., embedded Python/Lua):** Rejected as overly complex for defining simple transfer rules. A declarative configuration format (like YAML) is more user-friendly and safer.

## Consequences

*   Requires a well-defined schema for the transfer rules in the configuration file.
*   The `Configuration Manager` needs to parse and validate these rules.
*   The `Analysis Engine` needs logic to match files against the source and filter criteria defined in the rules.
*   The `Action Executor` needs to interpret the rule associated with an `ActionItem` to determine the correct source, destination, action type, and options for the transfer (using logic from ADR-005 Revised).
*   The CLI needs commands to manage and list these transfer rules.
*   Initial implementation might support a subset of source/destination types (e.g., local, OneDrive, GDrive) and filter options, with others added later.