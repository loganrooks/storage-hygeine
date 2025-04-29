# Storage Hygiene System - Architecture Report

**Version:** 1.0
**Date:** 2025-04-29
**Status:** Proposed

## 1. Overview

This document outlines the proposed architecture for the Storage Hygiene System. The system aims to scan local and cloud storage, identify potential files for deletion or organization (duplicates, large/old files, similar content, temporary files, etc.), allow user review, execute actions, and facilitate cloud migration (OneDrive to Google Drive). It prioritizes modularity, scalability, security, and cross-platform compatibility (Windows/Linux).

## 2. Goals & Requirements

*   Scan local drives, external drives, OneDrive, Google Drive.
*   Identify files based on configurable rules:
    *   Exact duplicates (hash).
    *   Similar content (perceptual hash for images/video, fuzzy hash for docs, acoustic fingerprint for audio).
    *   Large size, old age (last access/modified).
    *   Temporary files, cache files, log files, build files, zero-byte files, empty folders.
    *   Potentially corrupt files (header checks, type-specific validation).
    *   Files in Recycle Bin/Trash.
*   Calculate disorganization metrics.
*   Provide a user interface for reviewing suggestions and confirming actions.
*   Execute actions: delete (permanent/trash), move local, migrate OneDrive (non-media) to Google Drive.
*   Securely manage cloud credentials (no hardcoding).
*   Operate efficiently on potentially terabyte-scale storage (parallelism, incremental scans).
*   Be cross-platform (Windows, Linux).
*   (Post-MVP) Integrate AI for organization suggestions.

## 3. High-Level Architecture

The system employs a modular, service-based architecture implemented primarily in Python. Key components interact via a central metadata store (DuckDB) and configuration manager. A local web server provides the primary user interface.

[See Diagram: Storage Hygiene System (Detailed) - 2025-04-29 19:34:11 in `memory-bank/mode-specific/architect.md`]

## 4. Core Components

*   **Scanner Service (Pool):** Parallelized component to traverse sources, gather metadata (including basic hashes), perform incremental checks, and write to DuckDB.
*   **Analysis Engine:** Processes metadata from DuckDB, applies rules, performs similarity/corruption checks, calculates metrics, updates flags in DuckDB. Manages CPU-intensive analysis tasks.
*   **Staging & Review UI (Web App):** Local web server (FastAPI) and browser frontend (JS framework) providing the main interface for review, configuration, and action confirmation. Interacts with DuckDB via the backend API.
*   **Action Executor:** Reads confirmed actions from DuckDB and executes them (delete, move, migrate) using appropriate APIs/libraries. Handles retries and logging.
*   **Configuration Manager:** Manages settings (YAML/JSON) and securely handles credentials via the OS Keychain (`keyring` library).
*   **Metadata Store (DuckDB):** Central embedded database storing file metadata, analysis flags, user decisions, and action status.
*   **AI Organization Assistant (Optional, Post-MVP):** Interacts with Vertex AI (Gemini) using metadata summaries for suggestions.

## 5. Key Architectural Decisions (See ADRs for details)

*   **UI Approach:** Phased CLI Core + Web App UI (ADR-001)
*   **Credential Management:** OS Keychain via `keyring` (ADR-002)
*   **Metadata Storage:** DuckDB (ADR-003)
*   **Incremental Scans:** Mod Time/Size Comparison (ADR-004)
*   **Cloud Migration:** Direct SDKs (Primary) + Optional `rclone` (ADR-005)
*   **AI Integration:** Post-MVP (ADR-006)

## 6. Data Models

*   **FileMetadata:** Stores detailed information about each scanned file/folder in DuckDB.
*   **ActionItem:** Stores user-confirmed actions and their status in DuckDB.

[See Data Models - 2025-04-29 19:34:11 in `memory-bank/mode-specific/architect.md`]

## 7. Key Patterns & Strategies

*   **Modularity:** Components are distinct with clear responsibilities.
*   **Scalability:** Parallel scanning, incremental updates, efficient DuckDB queries.
*   **Security:** OS Keychain for credentials, no hardcoding.
*   **Cross-Platform:** Python core, `pathlib`, `keyring`, Web UI.
*   **Data Flow:** Centralized metadata store (DuckDB) facilitates communication.
*   **Error Handling:** Retry logic (exponential backoff), detailed logging.
*   **User Experience:** Rich Web UI for review, CLI for core operations/scripting.

## 8. Future Considerations

*   Implementing AI Assistant.
*   Adding support for more cloud providers.
*   Advanced corruption detection methods.
*   Real-time filesystem monitoring (`watchdog`).
*   More sophisticated disorganization heuristics.