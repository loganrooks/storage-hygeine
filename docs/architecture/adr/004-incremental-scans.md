# ADR-004: Incremental Scans

**Date:** 2025-04-29
**Status:** Proposed

## Context

Scanning potentially terabytes of storage containing millions or billions of files is time-consuming. Re-scanning and re-analyzing all files on every run is inefficient, especially if only a small fraction of files have changed. The system needs a mechanism to speed up subsequent scans by focusing only on changes.

## Decision

We will implement incremental scanning primarily based on **comparing file modification times and sizes** against the metadata stored in the DuckDB database from the previous scan.
1.  During a scan, for each file encountered, the `Scanner Service` will query DuckDB for an existing record matching the file path.
2.  If a record exists, the scanner compares the current file's modification time and size with the stored values.
3.  If the modification time or size differs, or if the file is new (no existing record), the file is considered changed/new and requires full metadata gathering and hashing. Its `last_seen` timestamp in the DB is updated.
4.  If the modification time and size match the stored record, the file is considered unchanged. The scanner can skip re-calculating hashes and only update the `last_seen` timestamp in the DB record.
5.  Files present in the DB but not found during the current scan (and whose `last_seen` timestamp is from a previous scan) can be marked as deleted or missing.
6.  A full, non-incremental rescan option will always be available to the user.

## Rationale

*   **Performance Improvement:** This approach significantly reduces the workload for subsequent scans by avoiding redundant I/O (reading file content for hashing) and computation (hash calculation) for unchanged files, which often constitute the vast majority of the filesystem.
*   **Simplicity and Robustness:** Comparing modification times and sizes is a relatively simple, fast, and reliable method for detecting changes on most filesystems. It avoids the complexities and potential platform inconsistencies of filesystem event monitoring.
*   **Database Integration:** Leverages the existing DuckDB metadata store efficiently. Checking for existing records and comparing timestamps/sizes are fast database operations.

## Alternatives Considered

*   **Full Rescans Only:** Rejected due to unacceptable performance for large filesystems on subsequent runs.
*   **Filesystem Event Monitoring (e.g., using `watchdog` library):** Rejected for V1. While providing near real-time change detection, it adds significant complexity:
    *   Requires a persistent background process.
    *   Can be resource-intensive.
    *   Handling buffer overflows or missed events during high filesystem activity requires careful implementation.
    *   Platform inconsistencies exist despite abstraction libraries.
    *   Less suitable for a tool designed for periodic hygiene scans rather than continuous monitoring.
*   **Hashing All Files and Comparing Hashes:** Rejected as it negates the performance benefit; hashing all files is the most time-consuming part of a full scan.

## Consequences

*   Relies on filesystem modification times being reasonably accurate. Files modified in ways that don't update the mtime (rare for user files) might be missed by incremental scans (though a full rescan would catch them).
*   Requires storing modification time and size accurately in the DuckDB database.
*   The `Scanner Service` logic becomes slightly more complex as it needs to query the database and compare metadata before deciding whether to perform a full metadata collection/hash.
*   A mechanism is needed to handle files that were present in the last scan but are missing in the current one (mark as deleted in the DB).