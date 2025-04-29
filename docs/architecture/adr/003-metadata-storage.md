# ADR-003: Metadata Storage

**Date:** 2025-04-29
**Status:** Proposed

## Context

The Storage Hygiene System needs to store metadata about potentially millions or billions of files scanned across local and cloud storage. This metadata includes file paths, sizes, dates, hashes (SHA-256, perceptual, fuzzy), analysis flags, user decisions, and action status. The system requires efficient querying for analysis (finding duplicates, filtering by flags/size/date, calculating metrics) and updates (marking flags, recording decisions/status). The storage solution must handle potentially terabyte-scale metadata efficiently for a single-user desktop application.

## Decision

We will use **DuckDB** as the embedded database for storing all file metadata (`FileMetadata` table) and user action items (`ActionItem` table).

## Rationale

*   **Performance for Analytical Queries:** DuckDB is an embedded OLAP (Online Analytical Processing) database optimized for analytical queries. This is ideal for the `Analysis Engine`'s tasks, such as finding duplicates based on hashes (`GROUP BY sha256_hash HAVING COUNT(*) > 1`), filtering files by various criteria (flags, size, date), calculating disorganization metrics, and identifying similarity groups. Its columnar storage format generally outperforms row-oriented databases like SQLite for these types of queries on large datasets.
*   **Embedded & Simple:** Like SQLite, DuckDB runs embedded within the application process, requiring no separate database server installation or management, simplifying deployment for a desktop tool.
*   **Scalability:** DuckDB is designed to handle larger-than-memory datasets effectively, spilling to disk when necessary. This is crucial for potentially scanning terabytes of storage resulting in large metadata tables.
*   **Rich SQL Support & Python Integration:** Offers extensive SQL support, including window functions useful for analysis, and excellent Python integration (easy data loading/querying, compatibility with Pandas/Polars DataFrames if needed).
*   **Concurrency:** While primarily single-process focused, it offers mechanisms for managing writes from multiple processes (e.g., using a single writer process fed by a queue from parallel scanners), mitigating some potential bottlenecks seen with SQLite under heavy parallel writes.

## Alternatives Considered

*   **SQLite:** Rejected. While simple and embedded, its row-oriented nature is less performant for the analytical queries required. Write performance can become a bottleneck with highly parallel scanners due to database locking.
*   **File-Based Storage (e.g., Parquet, CSV, JSON Lines):** Rejected. Lack transactional guarantees for updates (e.g., marking analysis flags, recording user decisions). Querying requires loading data into memory (e.g., using Pandas/Polars) or implementing complex indexing/query logic manually. Updates often require rewriting large portions of files.
*   **Full Relational Database (e.g., PostgreSQL, MySQL):** Rejected. Overkill for a single-user desktop application. Requires separate installation, configuration, and management, significantly increasing deployment complexity.
*   **In-Memory Storage (e.g., Python dictionaries, Pandas DataFrames):** Rejected. Not feasible for terabyte-scale metadata which will likely exceed available RAM.

## Consequences

*   Requires the `duckdb` Python library as a dependency.
*   The database schema (`FileMetadata`, `ActionItem` tables) needs to be defined and managed (potentially using simple SQL scripts or an embedded migration tool if schema evolves significantly).
*   Care must be taken when handling writes from parallel processes (Scanner Pool) to avoid contention, likely requiring a single writer process/thread fed by a queue.
*   While generally robust, being a newer project than SQLite, there might be fewer resources or community solutions for specific edge-case issues, although its adoption is growing rapidly.