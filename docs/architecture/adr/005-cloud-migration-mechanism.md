# ADR-005: Cloud/Local Transfer Mechanism (Revised)

**Date:** 2025-04-29
**Status:** Accepted (Revised based on user feedback)

## Context

The system needs to perform file transfer actions, such as moving files to the trash, moving files between local directories, migrating files between cloud storage providers (e.g., OneDrive to Google Drive), or backing up local files to the cloud. These transfers need to be configurable, handle potentially large files/datasets, and manage errors robustly. The initial proposal focused specifically on OneDrive-to-GDrive migration.

## Decision

We will implement a generalized transfer mechanism within the `Action Executor` component based on configurable rules (see ADR-007). The core transfer logic will:
1.  Use direct Python libraries (`os`, `shutil`, `pathlib`) for local-to-local moves/copies.
2.  Use official Cloud SDKs (e.g., Microsoft Graph, Google Drive API) for operations involving cloud storage (cloud-to-local, local-to-cloud, cloud-to-cloud).
3.  Stage files via a local temporary directory when a direct transfer path is not available or efficient (e.g., for cloud-to-cloud transfers, or potentially for verification steps).
4.  Implement robust error handling, including retries with exponential backoff (`tenacity`) for network/API issues, detailed logging, and status updates in the `ActionItem` table in DuckDB.
5.  Support batching for API calls where available.
6.  Optionally, offer integration with `rclone` as an alternative backend for users who have it installed and configured, selectable via configuration.

## Rationale

*   **Flexibility:** This approach supports various transfer scenarios (local, cloud, mixed) defined by user configuration (ADR-007), rather than being hardcoded to a specific path like OneDrive-to-GDrive.
*   **Control & Integration:** Using SDKs and standard Python libraries directly provides maximum control over the process, error handling, progress reporting (via CLI), and logging within the application framework.
*   **Reliability:** Staging via a local temporary directory for indirect transfers (like cloud-to-cloud) improves resilience to transient network issues and allows for potential verification steps.
*   **Maintainability:** Consolidates transfer logic within the `Action Executor`, using appropriate tools (SDKs, `shutil`) based on the source and destination defined in the action rule.
*   **Power-User Option:** Retaining optional `rclone` integration caters to advanced users without making it a core dependency.

## Alternatives Considered

*   **Direct Cloud-to-Cloud Transfer APIs:** Generally unavailable or unreliable via standard user APIs for arbitrary transfers between providers like OneDrive and Google Drive.
*   **`rclone` Only:** Rejected as the primary method due to external dependency, configuration complexity for standard users, and difficulty integrating detailed progress/error feedback directly into the application's CLI/logs.
*   **Using Native Sync Clients:** Rejected. Not suitable for controlled, filtered, bulk transfer operations.

## Consequences

*   The `Action Executor` becomes more complex as it needs to handle different transfer types (local, cloud-in, cloud-out) based on the source/destination specified in the `ActionItem` and associated rule.
*   Requires dependencies on relevant Cloud SDKs (e.g., `google-api-python-client`, `msgraph-core`, potentially others if more providers are supported).
*   Local temporary disk space is required for staging indirect transfers. The application must manage this space and check availability.
*   Network bandwidth usage can be significant for cloud operations.
*   Robust implementation of authentication (via ADR-002), batching, pagination, rate limiting, and error handling for each supported SDK is critical.
*   If `rclone` integration is implemented, requires logic to detect `rclone`, manage its configuration/authentication context, and execute/monitor its processes.
*   Need clear configuration options for conflict resolution during transfers (skip, rename, overwrite).