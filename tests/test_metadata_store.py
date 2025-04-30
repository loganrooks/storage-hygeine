from datetime import datetime, timezone
import pytest
import os
import duckdb
from pathlib import Path
from storage_hygiene.metadata_store import MetadataStore
# from storage_hygiene.config_manager import ConfigManager # If needed later


def test_metadata_store_initialization(tmp_path):
    """
    Test that MetadataStore initializes and creates the database file.
    TDD Anchor: [MS_Init]
    """
    db_file = tmp_path / "test_metadata.db"
    assert not db_file.exists() # Ensure file doesn't exist initially

    # --- Action ---
    # Use a context manager to ensure the connection is closed
    with MetadataStore(db_path=db_file) as store:
        # --- Assertions ---
        # 1. Check if the database file was created
        assert db_file.exists(), "Database file should be created on initialization."

        # 2. Check if the connection attribute exists and is open
        assert hasattr(store, 'conn'), "Store should have a connection attribute."
        assert store.conn is not None, "Connection should be established."

        # Verification of file validity is implicitly done by the successful
        # connection within MetadataStore.__init__ and the __exit__ closing it.

    # 4. Check connection is closed after exiting context manager
    # Accessing store.conn after __exit__ might be tricky if it's set to None.
    # Instead, we can try connecting again; if it fails because it's locked,
    # it wasn't closed properly. Or rely on the logging inside close().
    # For simplicity, we'll assume the __exit__ works for now.
    # A more robust test might involve mocking duckdb.connect.close().
def test_initialize_schema(tmp_path):
    """
    Test that the database schema (files table) is created correctly.
    TDD Anchor: [MS_Schema]
    """
    db_file = tmp_path / "test_metadata.db"

    # --- Action ---
    # Initialize the store, which should trigger schema creation
    with MetadataStore(db_path=db_file) as store:
        # Explicitly call _initialize_schema if it's not called in __init__ yet
        # For now, assume __init__ handles it or we call it manually if needed
        # store._initialize_schema() # This method doesn't exist yet

        # --- Assertions ---
        # Use the store's connection to check the schema
        try:
            assert store.conn is not None, "Connection should be valid within the context."
            cursor = store.conn.cursor()

            # Check if 'files' table exists
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_name = 'files';")
            result = cursor.fetchone()
            assert result is not None, "Table 'files' should exist after initialization."
            assert result[0] == 'files'

            # Check for expected columns and types (adjust types as needed based on pseudocode/ADR)
            expected_columns = {
                'path': 'VARCHAR',          # Or TEXT
                'filename': 'VARCHAR',
                'size_bytes': 'BIGINT',     # Or INTEGER
                'last_modified': 'TIMESTAMP WITH TIME ZONE',
                'hash': 'VARCHAR',          # Assuming SHA-256 hex digest
                'last_scanned': 'TIMESTAMP WITH TIME ZONE',
                # Add other columns from pseudocode/ADR if necessary
                # 'creation_time': 'TIMESTAMP',
                # 'last_access_time': 'TIMESTAMP',
                # 'owner': 'VARCHAR',
                # 'group': 'VARCHAR',
                # 'permissions': 'VARCHAR',
            }

            cursor.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'files' ORDER BY column_name;")
            actual_columns = dict(cursor.fetchall())

            assert set(actual_columns.keys()) == set(expected_columns.keys()), \
                   f"Column names mismatch. Expected: {set(expected_columns.keys())}, Got: {set(actual_columns.keys())}"

            for col_name, expected_type in expected_columns.items():
                # DuckDB type names can vary slightly (e.g., INTEGER vs INT). Be flexible or normalize.
                # For now, we'll do a basic check. Might need refinement.
                assert col_name in actual_columns, f"Expected column '{col_name}' not found."
                # Making type comparison case-insensitive and allowing for synonyms like BIGINT/INT8
                actual_type_upper = actual_columns[col_name].upper()
                expected_type_upper = expected_type.upper()
                # Simple synonym check
                if expected_type_upper == 'BIGINT':
                    assert actual_type_upper in ('BIGINT', 'INT8'), f"Type mismatch for '{col_name}'. Expected: {expected_type}, Got: {actual_columns[col_name]}"
                elif expected_type_upper == 'VARCHAR':
                     assert actual_type_upper in ('VARCHAR', 'TEXT'), f"Type mismatch for '{col_name}'. Expected: {expected_type}, Got: {actual_columns[col_name]}"
                elif expected_type_upper == 'TIMESTAMP WITH TIME ZONE':
                    # Check if it starts with the expected type, ignoring potential precision differences
                    assert actual_type_upper.startswith('TIMESTAMP WITH TIME ZONE'), f"Type mismatch for '{col_name}'. Expected: {expected_type}, Got: {actual_columns[col_name]}"
                else:
                    assert actual_type_upper == expected_type_upper, f"Type mismatch for '{col_name}'. Expected: {expected_type}, Got: {actual_columns[col_name]}"

            # Check primary key (assuming 'path' is PK based on pseudocode)
            cursor.execute("""
                SELECT constraint_type
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                WHERE tc.table_name = 'files' AND kcu.column_name = 'path' AND tc.constraint_type = 'PRIMARY KEY';
            """)
            pk_result = cursor.fetchone()
            assert pk_result is not None and pk_result[0] == 'PRIMARY KEY', "Column 'path' should be the PRIMARY KEY."


            # cursor.close() # Closing cursor is good practice, but often handled by connection close
            # No need to close conn_verify as we are using store.conn managed by context manager
        except Exception as e:
            pytest.fail(f"Error verifying schema using store connection: {e}")
def test_upsert_file_record_insert(tmp_path):
    """
    Test inserting a new file record using upsert_file_record.
    TDD Anchor: [MS_AddRecord]
    """
    db_file = tmp_path / "test_metadata.db"
    test_path = "/path/to/test/file.txt"
    now = datetime.now(timezone.utc)

    file_data = {
        'path': test_path,
        'filename': 'file.txt',
        'size_bytes': 1024,
        'last_modified': now,
        'hash': 'fakehash123',
        'last_scanned': now,
    }

    with MetadataStore(db_path=db_file) as store:
        # --- Action ---
        store.upsert_file_record(file_data) # This method doesn't exist yet

        # --- Assertions ---
        # Verify the record exists in the database with the correct data
        try:
            cursor = store.conn.cursor()
            cursor.execute("SELECT path, filename, size_bytes, last_modified, hash, last_scanned FROM files WHERE path = ?", (test_path,))
            result = cursor.fetchone()

            assert result is not None, "Record should have been inserted."
            assert result[0] == file_data['path']
            assert result[1] == file_data['filename']
            assert result[2] == file_data['size_bytes']
            # Timestamp comparison: DuckDB TIMESTAMPTZ should return aware objects.
            # Compare directly, ensuring both are UTC.
            retrieved_last_modified = result[3]
            retrieved_last_scanned = result[5]
            # Ensure retrieved are aware and convert to UTC if necessary (though they should be UTC)
            if retrieved_last_modified.tzinfo is None:
                 pytest.fail("Retrieved last_modified is not timezone-aware")
            if retrieved_last_scanned.tzinfo is None:
                 pytest.fail("Retrieved last_scanned is not timezone-aware")

            assert abs(retrieved_last_modified.astimezone(timezone.utc) - file_data['last_modified']).total_seconds() < 1, "last_modified timestamp mismatch"
            assert result[4] == file_data['hash']
            assert abs(retrieved_last_scanned.astimezone(timezone.utc) - file_data['last_scanned']).total_seconds() < 1, "last_scanned timestamp mismatch"

        except Exception as e:
            pytest.fail(f"Error verifying inserted record: {e}")
def test_upsert_file_record_update(tmp_path):
    """
    Test updating an existing file record using upsert_file_record.
    TDD Anchor: [MS_UpdateRecord]
    """
    db_file = tmp_path / "test_metadata.db"
    test_path = "/path/to/update/file.txt"
    now = datetime.now(timezone.utc)
    later = datetime.now(timezone.utc) # Ensure it's slightly different

    initial_data = {
        'path': test_path,
        'filename': 'file.txt',
        'size_bytes': 1024,
        'last_modified': now,
        'hash': 'initial_hash',
        'last_scanned': now,
    }
    updated_data = {
        'path': test_path, # Same path
        'filename': 'file_renamed.txt', # Different filename
        'size_bytes': 2048,             # Different size
        'last_modified': later,           # Different timestamp
        'hash': 'updated_hash',         # Different hash
        'last_scanned': later,            # Different timestamp
    }

    with MetadataStore(db_path=db_file) as store:
        # --- Action 1: Insert initial record ---
        store.upsert_file_record(initial_data)

        # --- Action 2: Update the record ---
        store.upsert_file_record(updated_data)

        # --- Assertions ---
        # Verify the record reflects the updated data
        try:
            cursor = store.conn.cursor()
            cursor.execute("SELECT path, filename, size_bytes, last_modified, hash, last_scanned FROM files WHERE path = ?", (test_path,))
            result = cursor.fetchone()

            assert result is not None, "Record should exist after update."
            assert result[0] == updated_data['path']
            assert result[1] == updated_data['filename'], "Filename should be updated."
            assert result[2] == updated_data['size_bytes'], "Size should be updated."
            # Timestamp comparison
            retrieved_last_modified = result[3]
            retrieved_last_scanned = result[5]
            if retrieved_last_modified.tzinfo is None or retrieved_last_scanned.tzinfo is None:
                 pytest.fail("Retrieved timestamps should be timezone-aware")

            assert abs(retrieved_last_modified.astimezone(timezone.utc) - updated_data['last_modified']).total_seconds() < 1, "last_modified should be updated."
            assert result[4] == updated_data['hash'], "Hash should be updated."
            assert abs(retrieved_last_scanned.astimezone(timezone.utc) - updated_data['last_scanned']).total_seconds() < 1, "last_scanned should be updated."

            # Verify only one record exists for this path
            cursor.execute("SELECT COUNT(*) FROM files WHERE path = ?", (test_path,))
            count_result = cursor.fetchone()
            assert count_result[0] == 1, "Should only be one record for the given path after upsert."

        except Exception as e:
            pytest.fail(f"Error verifying updated record: {e}")
def test_query_files_by_path(tmp_path):
    """
    Test querying file records by path.
    TDD Anchor: [MS_Query]
    """
    db_file = tmp_path / "test_metadata.db"
    test_path1 = "/path/to/query/file1.txt"
    test_path2 = "/path/to/query/file2.log"
    now = datetime.now(timezone.utc)

    file_data1 = {
        'path': test_path1, 'filename': 'file1.txt', 'size_bytes': 100,
        'last_modified': now, 'hash': 'hash1', 'last_scanned': now
    }
    file_data2 = {
        'path': test_path2, 'filename': 'file2.log', 'size_bytes': 200,
        'last_modified': now, 'hash': 'hash2', 'last_scanned': now
    }

    with MetadataStore(db_path=db_file) as store:
        # --- Setup: Insert records ---
        store.upsert_file_record(file_data1)
        store.upsert_file_record(file_data2)

        # --- Action: Query by path ---
        results = store.query_files(criteria={'path': test_path1}) # Method doesn't exist yet

        # --- Assertions ---
        assert isinstance(results, list), "Query should return a list."
        assert len(results) == 1, "Should find exactly one record for the specific path."

        result = results[0]
        assert isinstance(result, dict), "Each result should be a dictionary."
        assert result['path'] == file_data1['path']
        assert result['filename'] == file_data1['filename']
        assert result['size_bytes'] == file_data1['size_bytes']
        assert result['hash'] == file_data1['hash']
        # Compare timestamps (ensure aware)
        if result['last_modified'].tzinfo is None or result['last_scanned'].tzinfo is None:
             pytest.fail("Retrieved timestamps should be timezone-aware")
        assert abs(result['last_modified'].astimezone(timezone.utc) - file_data1['last_modified']).total_seconds() < 1
        assert abs(result['last_scanned'].astimezone(timezone.utc) - file_data1['last_scanned']).total_seconds() < 1

        # --- Action: Query non-existent path ---
        results_nonexistent = store.query_files(criteria={'path': '/path/does/not/exist.txt'})

        # --- Assertions ---
        assert isinstance(results_nonexistent, list)
        assert len(results_nonexistent) == 0, "Should return empty list for non-existent path."
def test_query_files_multiple_criteria(tmp_path):
    """
    Test querying file records using multiple criteria (exact match).
    TDD Anchor: [MS_Query]
    """
    db_file = tmp_path / "test_metadata.db"
    now = datetime.now(timezone.utc)

    file_data1 = {
        'path': '/path/multi/file1.txt', 'filename': 'file1.txt', 'size_bytes': 100,
        'last_modified': now, 'hash': 'hash_A', 'last_scanned': now
    }
    file_data2 = {
        'path': '/path/multi/file2.txt', 'filename': 'file2.txt', 'size_bytes': 200,
        'last_modified': now, 'hash': 'hash_B', 'last_scanned': now
    }
    file_data3 = { # Same hash as file1, different filename
        'path': '/path/multi/another.log', 'filename': 'another.log', 'size_bytes': 300,
        'last_modified': now, 'hash': 'hash_A', 'last_scanned': now
    }

    with MetadataStore(db_path=db_file) as store:
        # --- Setup: Insert records ---
        store.upsert_file_record(file_data1)
        store.upsert_file_record(file_data2)
        store.upsert_file_record(file_data3)

        # --- Action: Query by hash AND filename ---
        results = store.query_files(criteria={'hash': 'hash_A', 'filename': 'file1.txt'})

        # --- Assertions ---
        assert isinstance(results, list)
        assert len(results) == 1, "Should find exactly one record matching both criteria."
        assert results[0]['path'] == file_data1['path']
        assert results[0]['hash'] == 'hash_A'
        assert results[0]['filename'] == 'file1.txt'

        # --- Action: Query by only hash (should return 2) ---
        results_hash_only = store.query_files(criteria={'hash': 'hash_A'})

        # --- Assertions ---
        assert isinstance(results_hash_only, list)
        assert len(results_hash_only) == 2, "Should find two records matching only the hash."
        paths_found = {r['path'] for r in results_hash_only}
        assert paths_found == {file_data1['path'], file_data3['path']}

        # --- Action: Query with non-matching criteria ---
        results_no_match = store.query_files(criteria={'hash': 'hash_A', 'filename': 'nonexistent.txt'})

        # --- Assertions ---
        assert isinstance(results_no_match, list)
        assert len(results_no_match) == 0, "Should find no records for non-matching criteria."