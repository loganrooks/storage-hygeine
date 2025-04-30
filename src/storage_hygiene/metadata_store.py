import duckdb
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MetadataStore:
    """
    Manages the DuckDB database connection and operations for file metadata.
    """
    def __init__(self, db_path: Path):
        """
        Initializes the MetadataStore, connecting to the DuckDB database.
        Creates the database file if it doesn't exist.

        Args:
            db_path: The path to the DuckDB database file.
        """
        self.db_path = db_path
        self.conn = None
        try:
            # Connect to the database (creates the file if it doesn't exist)
            self.conn = duckdb.connect(database=str(self.db_path), read_only=False)
            logger.info(f"Successfully connected to database: {self.db_path}")
            # Initialize schema
            self._initialize_schema()
        except Exception as e:
            logger.error(f"Failed to connect to database {self.db_path}: {e}")
            # Re-raise the exception or handle it as appropriate
            raise

    def close(self):
        """Closes the database connection if it's open."""
        if self.conn:
            try:
                self.conn.close()
                logger.info(f"Database connection closed for: {self.db_path}")
                self.conn = None
            except Exception as e:
                logger.error(f"Error closing database connection {self.db_path}: {e}")

    def __enter__(self):
        """Enter the runtime context related to this object."""
        # In this simple case, __init__ already establishes the connection.
        # If connection were deferred, it would happen here.
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the runtime context related to this object."""
        self.close()

    def _initialize_schema(self):
        """Creates the necessary tables if they don't exist."""
        if not self.conn:
            logger.error("Cannot initialize schema, no database connection.")
            return

        try:
            cursor = self.conn.cursor()
            # TDD Anchor: [MS_Schema] - Create files table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    path VARCHAR PRIMARY KEY,
                    filename VARCHAR,
                    size_bytes BIGINT,
                    last_modified TIMESTAMP WITH TIME ZONE,
                    hash VARCHAR,
                    last_scanned TIMESTAMP WITH TIME ZONE
                );
            """)
            # Consider adding indexes later for performance if needed, e.g., on hash or last_scanned
            # cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_hash ON files (hash);")
            logger.info("Database schema initialized successfully (files table).")
            cursor.close() # Close cursor after use
        except Exception as e:
            logger.error(f"Failed to initialize database schema: {e}")
            # Decide if this should raise an exception or just log
            raise # Re-raise for now, as schema is critical

    def upsert_file_record(self, file_metadata: dict):
        """
        Inserts or updates a file record in the database.
        Uses INSERT OR REPLACE based on the primary key 'path'.
        TDD Anchor: [MS_AddRecord], [MS_UpdateRecord]

        Args:
            file_metadata: A dictionary containing file metadata matching the table schema.
                           Expected keys: 'path', 'filename', 'size_bytes',
                                          'last_modified', 'hash', 'last_scanned'.
        """
        if not self.conn:
            logger.error("Cannot upsert record, no database connection.")
            # Or raise an exception? For now, log and return.
            return

        # Ensure all required keys are present (optional but good practice)
        required_keys = {'path', 'filename', 'size_bytes', 'last_modified', 'hash', 'last_scanned'}
        if not required_keys.issubset(file_metadata):
            missing = required_keys - set(file_metadata)
            logger.error(f"Missing required keys for upsert: {missing}")
            raise ValueError(f"Missing required keys for upsert: {missing}") # Raise error

        sql = """
            INSERT OR REPLACE INTO files (path, filename, size_bytes, last_modified, hash, last_scanned)
            VALUES (?, ?, ?, ?, ?, ?);
        """
        params = (
            file_metadata['path'],
            file_metadata['filename'],
            file_metadata['size_bytes'],
            file_metadata['last_modified'],
            file_metadata['hash'],
            file_metadata['last_scanned'],
        )

        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, params)
            self.conn.commit() # Explicitly commit changes
            logger.debug(f"Upserted record for path: {file_metadata['path']}")
            cursor.close()
        except Exception as e:
            logger.error(f"Failed to upsert record for path {file_metadata.get('path', 'N/A')}: {e}")
            # Consider rolling back if part of a larger transaction context
            # self.conn.rollback()
            raise # Re-raise the exception

    def query_files(self, criteria: dict) -> list[dict]:
        """
        Queries the 'files' table based on the provided criteria.
        Returns a list of matching records as dictionaries.
        TDD Anchor: [MS_Query]

        Args:
            criteria: A dictionary where keys are column names and values are
                      the values to filter by (currently only supports exact match).

        Returns:
            A list of dictionaries, where each dictionary represents a file record.
            Returns an empty list if no matches are found or in case of error.
        """
        if not self.conn:
            logger.error("Cannot query records, no database connection.")
            return []

        # Define valid columns for filtering to prevent potential issues
        valid_columns = {'path', 'filename', 'size_bytes', 'last_modified', 'hash', 'last_scanned'}
        where_clauses = []
        params = []

        if not criteria:
            # Return all records if no criteria specified
            # Alternatively, could raise an error or return empty list based on desired behavior.
            # Returning all for now, but this might be inefficient for large tables.
            logger.info("Query called with no criteria, returning all records.")
            sql = "SELECT path, filename, size_bytes, last_modified, hash, last_scanned FROM files;"
            # No params needed
        else:
            # Build WHERE clause dynamically for exact matches
            for key, value in criteria.items():
                if key in valid_columns:
                    # Use placeholders to prevent SQL injection
                    where_clauses.append(f"{key} = ?")
                    params.append(value)
                else:
                    logger.warning(f"Ignoring invalid query criterion: {key}")

            if not where_clauses:
                 logger.warning("No valid query criteria found after filtering.")
                 return [] # Return empty if only invalid criteria were provided

            sql = f"SELECT path, filename, size_bytes, last_modified, hash, last_scanned FROM files WHERE {' AND '.join(where_clauses)};"

        results = []
        try:
            cursor = self.conn.cursor()
            logger.debug(f"Executing query: {sql} with params: {params}")
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description] # Get column names

            for row in rows:
                results.append(dict(zip(columns, row)))

            cursor.close()
            logger.debug(f"Query returned {len(results)} records.")

        except Exception as e:
            logger.error(f"Failed to execute query with criteria {criteria}: {e}")
            # Return empty list on error, or re-raise?
            return [] # Returning empty list for now

        return results