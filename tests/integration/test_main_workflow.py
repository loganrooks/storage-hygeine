# tests/integration/test_main_workflow.py
import pytest
import subprocess
import sys
import os
import hashlib # <-- Add import
from pathlib import Path
import time
import duckdb # Import duckdb instead of sqlite3
import yaml

# Define paths relative to the project root (assuming pytest runs from root)
PROJECT_ROOT = Path(__file__).parent.parent.parent
SRC_DIR = PROJECT_ROOT / "src"
MAIN_SCRIPT_PATH = SRC_DIR / "storage_hygiene" / "main.py"

# Ensure the src directory is in the Python path for imports within the script
sys.path.insert(0, str(SRC_DIR))

# Helper function to create dummy files
def create_dummy_file(path: Path, size_mb: int = 0, content: str = None, mtime_days_ago: int = None):
    """Creates a dummy file with optional size and modification time."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if content is not None:
        path.write_text(content)
    elif size_mb > 0:
        with open(path, "wb") as f:
            f.seek((size_mb * 1024 * 1024) - 1)
            f.write(b"\0")
    else:
        path.touch()

    if mtime_days_ago is not None:
        past_time = time.time() - (mtime_days_ago * 86400)
        os.utime(path, (past_time, past_time))

@pytest.fixture
def setup_test_environment(tmp_path):
    """Sets up a temporary environment for integration testing."""
    scan_dir = tmp_path / "scan_dir"
    staging_dir = tmp_path / "staging_dir"
    db_path = tmp_path / "test_metadata.db"
    config_path = tmp_path / "test_config.yaml"

    # Create directories
    scan_dir.mkdir()
    staging_dir.mkdir()

    # Create sample files
    create_dummy_file(scan_dir / "file1.txt", content="duplicate_content")
    create_dummy_file(scan_dir / "subdir" / "file2.txt", content="duplicate_content") # Duplicate
    create_dummy_file(scan_dir / "large_file.bin", size_mb=15) # Large file
    create_dummy_file(scan_dir / "old_file.log", mtime_days_ago=400) # Old file
    create_dummy_file(scan_dir / "normal_file.txt", content="unique")

    # Create config file
    config_data = {
        'analysis': {
            'rules': {
                'duplicate_files': {'enabled': True}, # Corrected key
                'large_files': {'enabled': True, 'min_size_mb': 10}, # Corrected key
                'old_files': {'enabled': True, 'max_days': 365} # Corrected key name
            }
        },
        'action_executor': {
            'staging_dir': str(staging_dir),
            # 'dry_run': False # Let CLI override this
        }
    }
    with open(config_path, 'w') as f:
        yaml.dump(config_data, f)

    return scan_dir, staging_dir, db_path, config_path

def test_main_workflow_dry_run(setup_test_environment, capsys):
    """Tests the main workflow in dry-run mode."""
    scan_dir, staging_dir, db_path, config_path = setup_test_environment

    # Command to run the main script
    cmd = [
        sys.executable, # Use the current Python interpreter
        "-m", "storage_hygiene.main", # Execute as a module
        "--config", str(config_path),
        "--db-path", str(db_path),
        "--dry-run", # Enable dry run via CLI
        str(scan_dir) # Target directory
    ]

    # Get current environment and update PYTHONPATH for the subprocess
    env = os.environ.copy()
    # Ensure src directory is in PYTHONPATH for the subprocess
    python_path = env.get('PYTHONPATH', '')
    src_path_str = str(SRC_DIR)
    if src_path_str not in python_path.split(os.pathsep):
        env['PYTHONPATH'] = f"{src_path_str}{os.pathsep}{python_path}" if python_path else src_path_str

    # Execute the script as a subprocess with the modified environment
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT, env=env)

    # Print stdout/stderr for debugging if the test fails
    print("STDOUT:\n", result.stdout)
    print("STDERR:\n", result.stderr)

    # Assertions
    assert result.returncode == 0, f"Script exited with error code {result.returncode}"

    # Check logs (stderr) for key workflow steps
    assert "Starting Storage Hygiene System..." in result.stderr
    assert f"Loading configuration from: {config_path}" in result.stderr
    assert "Dry run mode enabled via CLI." in result.stderr
    assert f"Initializing metadata store at: {db_path}" in result.stderr
    assert f"Scanning target directories: {scan_dir}" in result.stderr
    assert f"Scanning {scan_dir}..." in result.stderr
    assert "Scanning phase complete." in result.stderr
    assert "Initializing analysis engine..." in result.stderr
    assert "Running analysis..." in result.stderr
    # Check analysis summary (stderr)
    assert "Analysis complete. Found 3 potential actions." in result.stderr # 1 dup pair -> 1 action, 1 large, 1 old
    assert "- stage_duplicate: 1 files" in result.stderr # One of the duplicates should be marked
    assert "- review_large: 1 files" in result.stderr
    assert "- review_old: 1 files" in result.stderr
    assert "Initializing action executor..." in result.stderr
    assert "Executing actions... (Dry Run: True)" in result.stderr
    # Check specific dry-run action print statements (stdout)
    assert "[DRY RUN] Would move" in result.stdout # General check for dry run output
    assert "Staging duplicate:" in result.stdout
    assert "Staging large file:" in result.stdout
    assert "Staging old file:" in result.stdout
    assert "Action execution complete." in result.stderr
    assert "Storage Hygiene System finished successfully." in result.stderr

    # Check database content (basic check using duckdb)
    assert db_path.exists()
    conn = duckdb.connect(database=str(db_path), read_only=True) # Connect using duckdb
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM files") # Use correct table name 'files'
    count = cursor.fetchone()[0]
    conn.close()
    assert count == 5, f"Expected 5 files in metadata, found {count}"

    # Check that staging directory is empty (dry run)
    assert not any(staging_dir.iterdir()), "Staging directory should be empty in dry run"
def test_main_workflow_non_dry_run(setup_test_environment, capsys):
    """Tests the main workflow with dry_run=False, verifying file movement."""
    scan_dir, staging_dir, db_path, config_path = setup_test_environment

    # Expected staging subdirectories (based on ActionExecutor logic)
    duplicate_stage_dir = staging_dir / "duplicates"
    large_stage_dir = staging_dir / "large_files" # Corrected name
    old_stage_dir = staging_dir / "old_files"   # Corrected name

    # Original file paths
    original_dup_src = scan_dir / "subdir" / "file2.txt"
    original_large_src = scan_dir / "large_file.bin"
    original_old_src = scan_dir / "old_file.log"
    original_kept_dup_src = scan_dir / "file1.txt"
    original_normal_src = scan_dir / "normal_file.txt"

    # Expected destination paths
    # Calculate hash for the duplicate file content (assuming fixture creates it)
    # Note: This assumes the content is known or consistent from the fixture.
    # If content varies, the fixture needs to provide it or the test needs adjustment.
    # For now, assume the content is 'duplicate_content' based on conftest.py setup
    dup_content = b"duplicate_content" # Match content from fixture (write_text encodes)
    dup_hash = hashlib.sha256(dup_content).hexdigest()

    # Construct the correct expected destination path for duplicates
    expected_dup_dest = duplicate_stage_dir / dup_hash[:2] / dup_hash / original_dup_src.name
    expected_large_dest = large_stage_dir / original_large_src.name
    expected_old_dest = old_stage_dir / original_old_src.name


    # Command to run the main script (NO --dry-run)
    cmd = [
        sys.executable,
        "-m", "storage_hygiene.main",
        "--config", str(config_path),
        "--db-path", str(db_path),
        # No --dry-run flag
        str(scan_dir) # Target directory
    ]

    # Get current environment and update PYTHONPATH for the subprocess
    env = os.environ.copy()
    python_path = env.get('PYTHONPATH', '')
    src_path_str = str(SRC_DIR)
    if src_path_str not in python_path.split(os.pathsep):
        env['PYTHONPATH'] = f"{src_path_str}{os.pathsep}{python_path}" if python_path else src_path_str

    # Execute the script
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT, env=env)

    # Print stdout/stderr for debugging if the test fails
    print("STDOUT:\n", result.stdout)
    print("STDERR:\n", result.stderr)

    # Assertions
    assert result.returncode == 0, f"Script exited with error code {result.returncode}"

    # Check logs (stderr) for key workflow steps (similar to dry run, but check dry_run status)
    assert "Starting Storage Hygiene System..." in result.stderr
    assert f"Loading configuration from: {config_path}" in result.stderr
    # assert "Dry run mode enabled via CLI." not in result.stderr # Ensure dry run is NOT mentioned as CLI enabled
    assert f"Initializing metadata store at: {db_path}" in result.stderr
    assert f"Scanning target directories: {scan_dir}" in result.stderr
    assert "Scanning phase complete." in result.stderr
    assert "Initializing analysis engine..." in result.stderr
    assert "Running analysis..." in result.stderr
    assert "Analysis complete. Found 3 potential actions." in result.stderr
    assert "Initializing action executor..." in result.stderr
    assert "Executing actions... (Dry Run: False)" in result.stderr # Verify Dry Run is False
    assert "Action execution complete." in result.stderr
    assert "Storage Hygiene System finished successfully." in result.stderr

    # Check that dry run specific messages are NOT in stdout
    assert "[DRY RUN]" not in result.stdout

    # Check database content
    assert db_path.exists()
    conn = duckdb.connect(database=str(db_path), read_only=True)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM files")
    count = cursor.fetchone()[0]
    # Check file records - paths should be updated for moved files
    cursor.execute("SELECT path FROM files WHERE filename = ?", (original_dup_src.name,))
    dup_path_in_db = cursor.fetchone()[0]
    cursor.execute("SELECT path FROM files WHERE filename = ?", (original_large_src.name,))
    large_path_in_db = cursor.fetchone()[0]
    cursor.execute("SELECT path FROM files WHERE filename = ?", (original_old_src.name,))
    old_path_in_db = cursor.fetchone()[0]
    conn.close()
    assert count == 5, f"Expected 5 files in metadata, found {count}"
    # Verify paths in DB point to the new staging locations
    assert Path(dup_path_in_db) == expected_dup_dest, f"DB path for duplicate incorrect: {dup_path_in_db}"
    assert Path(large_path_in_db) == expected_large_dest, f"DB path for large file incorrect: {large_path_in_db}"
    assert Path(old_path_in_db) == expected_old_dest, f"DB path for old file incorrect: {old_path_in_db}"


    # Check file system for actual movement
    # Files that should have been moved
    assert not original_dup_src.exists(), f"Original duplicate file {original_dup_src} should not exist"
    assert not original_large_src.exists(), f"Original large file {original_large_src} should not exist"
    assert not original_old_src.exists(), f"Original old file {original_old_src} should not exist"

    # Files that should exist in staging
    assert expected_dup_dest.exists(), f"Duplicate file should exist in staging: {expected_dup_dest}"
    assert expected_large_dest.exists(), f"Large file should exist in staging: {expected_large_dest}"
    assert expected_old_dest.exists(), f"Old file should exist in staging: {expected_old_dest}"

    # Check content integrity (optional but good)
    assert expected_dup_dest.read_text() == "duplicate_content"
    # Cannot easily check size/mtime here without more effort, focus on existence

    # Files that should remain untouched
    assert original_kept_dup_src.exists(), f"Kept duplicate file {original_kept_dup_src} should still exist"
    assert original_normal_src.exists(), f"Normal file {original_normal_src} should still exist"
def test_main_workflow_disabled_rules(setup_test_environment, capsys):
    """Tests the main workflow with specific analysis rules disabled in config."""
    scan_dir, staging_dir, db_path, config_path = setup_test_environment

    # --- Modify the config file ---
    with open(config_path, 'r') as f:
        config_data = yaml.safe_load(f)

    # Disable large and old file rules
    config_data['analysis']['rules']['large_files']['enabled'] = False
    config_data['analysis']['rules']['old_files']['enabled'] = False

    with open(config_path, 'w') as f:
        yaml.dump(config_data, f)
    # --- End config modification ---

    # Command to run the main script (dry run is sufficient here)
    cmd = [
        sys.executable,
        "-m", "storage_hygiene.main",
        "--config", str(config_path),
        "--db-path", str(db_path),
        "--dry-run",
        str(scan_dir)
    ]

    # Environment setup
    env = os.environ.copy()
    python_path = env.get('PYTHONPATH', '')
    src_path_str = str(SRC_DIR)
    if src_path_str not in python_path.split(os.pathsep):
        env['PYTHONPATH'] = f"{src_path_str}{os.pathsep}{python_path}" if python_path else src_path_str

    # Execute the script
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT, env=env)

    # Print stdout/stderr for debugging
    print("STDOUT:\n", result.stdout)
    print("STDERR:\n", result.stderr)

    # Assertions
    assert result.returncode == 0, f"Script exited with error code {result.returncode}"

    # Check logs for key workflow steps
    assert "Starting Storage Hygiene System..." in result.stderr
    assert f"Loading configuration from: {config_path}" in result.stderr
    assert "Dry run mode enabled via CLI." in result.stderr
    assert "Initializing analysis engine..." in result.stderr
    assert "Running analysis..." in result.stderr

    # Verify analysis summary reflects disabled rules
    # Only duplicate rule should be active and find 1 action
    assert "Analysis complete. Found 1 potential actions." in result.stderr
    assert "- stage_duplicate: 1 files" in result.stderr
    assert "- review_large:" not in result.stderr # Should not be present
    assert "- review_old:" not in result.stderr   # Should not be present

    # Verify action execution reflects only the duplicate action
    assert "Executing actions... (Dry Run: True)" in result.stderr
    assert "Staging duplicate:" in result.stdout
    assert "Staging large file:" not in result.stdout # Should not be present
    assert "Staging old file:" not in result.stdout   # Should not be present
    assert "Action execution complete." in result.stderr
    assert "Storage Hygiene System finished successfully." in result.stderr

    # Check that staging directory is empty (dry run)
    assert not any(staging_dir.iterdir()), "Staging directory should be empty in dry run"
def test_main_cli_arguments(setup_test_environment, capsys, tmp_path):
    """Tests that CLI arguments for config, db_path, and target are correctly used."""
    scan_dir, staging_dir_fixture, db_path_fixture, config_path_fixture = setup_test_environment

    # --- Create alternative paths and minimal config for this test ---
    alt_config_path = tmp_path / "alt_config.yaml"
    alt_db_path = tmp_path / "alt_db.db"
    alt_staging_dir = tmp_path / "alt_staging" # Need a staging dir in alt config
    alt_staging_dir.mkdir()

    alt_config_data = {
        'analysis': { 'rules': {} }, # Minimal valid config
        'action_executor': { 'staging_dir': str(alt_staging_dir) }
    }
    with open(alt_config_path, 'w') as f:
        yaml.dump(alt_config_data, f)
    # --- End alternative setup ---

    # Command using alternative paths via CLI arguments
    cmd = [
        sys.executable,
        "-m", "storage_hygiene.main",
        "--config", str(alt_config_path),   # Use alternative config path
        "--db-path", str(alt_db_path),     # Use alternative DB path
        "--dry-run",
        str(scan_dir)                      # Use scan_dir from fixture
    ]

    # Environment setup
    env = os.environ.copy()
    python_path = env.get('PYTHONPATH', '')
    src_path_str = str(SRC_DIR)
    if src_path_str not in python_path.split(os.pathsep):
        env['PYTHONPATH'] = f"{src_path_str}{os.pathsep}{python_path}" if python_path else src_path_str

    # Execute the script
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT, env=env)

    # Print stdout/stderr for debugging
    print("STDOUT:\n", result.stdout)
    print("STDERR:\n", result.stderr)

    # Assertions
    assert result.returncode == 0, f"Script exited with error code {result.returncode}"

    # Verify logs show the *alternative* paths being used
    assert f"Loading configuration from: {alt_config_path}" in result.stderr, "Alternative config path not found in logs"
    assert f"Initializing metadata store at: {alt_db_path}" in result.stderr, "Alternative DB path not found in logs"
    assert f"Scanning target directories: {scan_dir}" in result.stderr # Ensure correct target dir is logged

    # Verify the alternative DB file was created, not the fixture one
    assert alt_db_path.exists(), "Alternative DB file was not created"
    assert not db_path_fixture.exists(), "Fixture DB file should not have been created"

    # Verify the alternative staging dir was read from the alt config
    # Note: ActionExecutor is not initialized if no actions are found,
    # so we cannot reliably check its init log here.
    # We rely on the fact that if the script ran successfully with the alt config,
    # it must have parsed the staging_dir correctly if actions *were* generated.

    # Check that staging directory is empty (dry run)
    assert not any(alt_staging_dir.iterdir()), "Alternative staging directory should be empty in dry run"
def test_main_workflow_invalid_config_yaml(setup_test_environment, capsys):
    """Tests the main workflow with an invalid (malformed) YAML config file."""
    scan_dir, staging_dir, db_path, config_path = setup_test_environment

    # --- Overwrite config with invalid YAML ---
    invalid_yaml_content = """
analysis:
  rules:
    large_files: {{ enabled: True, min_size_mb: 10 }} # Escape braces for .format
   Missing closing bracket or incorrect indentation intentionally
action_executor:
    staging_dir: {staging_dir} # This one is for .format
"""
    with open(config_path, 'w') as f:
        f.write(invalid_yaml_content.format(staging_dir=str(staging_dir)))
    # --- End invalid config ---

    # Command to run the main script
    cmd = [
        sys.executable,
        "-m", "storage_hygiene.main",
        "--config", str(config_path),
        "--db-path", str(db_path),
        "--dry-run", # Dry run is fine, we expect failure before actions
        str(scan_dir)
    ]

    # Environment setup
    env = os.environ.copy()
    python_path = env.get('PYTHONPATH', '')
    src_path_str = str(SRC_DIR)
    if src_path_str not in python_path.split(os.pathsep):
        env['PYTHONPATH'] = f"{src_path_str}{os.pathsep}{python_path}" if python_path else src_path_str

    # Execute the script
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT, env=env)

    # Print stdout/stderr for debugging
    print("STDOUT:\n", result.stdout)
    print("STDERR:\n", result.stderr)

    # Assertions
    assert result.returncode != 0, "Script should exit with non-zero code for invalid config"

    # Check stderr for specific error messages
    # Expecting ConfigLoadError or similar from ConfigManager/main script
    assert "Error loading configuration" in result.stderr or "Failed to load configuration" in result.stderr or "ConfigLoadError" in result.stderr, "Expected config loading error message not found in stderr"
    # Check that it didn't proceed to later stages
    assert "Scanning target directories" not in result.stderr
    assert "Initializing metadata store" not in result.stderr
def test_main_workflow_non_existent_target(setup_test_environment, capsys, tmp_path):
    """Tests the main workflow when a non-existent target directory is provided."""
    scan_dir_fixture, staging_dir, db_path, config_path = setup_test_environment

    non_existent_dir = tmp_path / "this_dir_does_not_exist"

    # Command to run the main script, targeting the non-existent directory
    cmd = [
        sys.executable,
        "-m", "storage_hygiene.main",
        "--config", str(config_path),
        "--db-path", str(db_path),
        "--dry-run", # Dry run is fine, we expect failure before actions
        str(non_existent_dir) # Target non-existent directory
    ]

    # Environment setup
    env = os.environ.copy()
    python_path = env.get('PYTHONPATH', '')
    src_path_str = str(SRC_DIR)
    if src_path_str not in python_path.split(os.pathsep):
        env['PYTHONPATH'] = f"{src_path_str}{os.pathsep}{python_path}" if python_path else src_path_str

    # Execute the script
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT, env=env)

    # Print stdout/stderr for debugging
    print("STDOUT:\n", result.stdout)
    print("STDERR:\n", result.stderr)

    # Assertions
    assert result.returncode != 0, "Script should exit with non-zero code for non-existent target"

    # Check stderr for specific warning/error messages related to the target directory
    assert f"Target directory not found or is not a directory: {non_existent_dir}. Skipping." in result.stderr, "Expected non-existent target directory warning message not found in stderr"
    assert "No valid target directories found to scan." in result.stderr, "Expected 'No valid target directories' error message not found in stderr"
    # Check that it didn't proceed to later stages (Scanner init happens, but scan loop doesn't run)
    # assert "Scanning target directories" not in result.stderr # This log happens before the check
    # assert "Initializing metadata store" not in result.stderr # Store IS initialized before target check
def test_main_workflow_scan_variations(setup_test_environment, capsys, tmp_path):
    """Tests scanning with empty directories and mixed content."""
    scan_dir_fixture, staging_dir, db_path_fixture, config_path = setup_test_environment # Use fixture config

    # --- Create specific scan directories for this test ---
    scan_dir_empty = tmp_path / "scan_empty"
    scan_dir_mixed = tmp_path / "scan_mixed"
    scan_dir_empty.mkdir()
    scan_dir_mixed.mkdir()
    (scan_dir_mixed / "empty_subdir").mkdir() # Create an empty subdirectory
    create_dummy_file(scan_dir_mixed / "file_a.txt", content="content a")
    create_dummy_file(scan_dir_mixed / "subdir" / "file_b.txt", content="content b")
    # --- End specific scan setup ---

    # --- Test 1: Scan Empty Directory ---
    db_path_empty = tmp_path / "empty_scan.db" # Use a specific DB for this test part
    cmd_empty = [
        sys.executable, "-m", "storage_hygiene.main",
        "--config", str(config_path), "--db-path", str(db_path_empty), "--dry-run",
        str(scan_dir_empty) # Target empty directory
    ]
    env = os.environ.copy()
    python_path = env.get('PYTHONPATH', '')
    src_path_str = str(SRC_DIR)
    if src_path_str not in python_path.split(os.pathsep):
        env['PYTHONPATH'] = f"{src_path_str}{os.pathsep}{python_path}" if python_path else src_path_str

    print(f"\n--- Running Scan on Empty Directory: {scan_dir_empty} ---")
    result_empty = subprocess.run(cmd_empty, capture_output=True, text=True, cwd=PROJECT_ROOT, env=env)
    print("STDOUT (Empty):\n", result_empty.stdout)
    print("STDERR (Empty):\n", result_empty.stderr)

    assert result_empty.returncode == 0, "Script failed on empty directory scan"
    assert f"Scanning {scan_dir_empty}..." in result_empty.stderr
    assert "Scanning phase complete." in result_empty.stderr
    # Analysis should find 0 actions as no files were scanned
    assert "Analysis complete. Found 0 potential actions." in result_empty.stderr
    assert "Executing actions..." not in result_empty.stderr # No actions to execute

    # Check DB - should be created but empty
    assert db_path_empty.exists()
    conn = duckdb.connect(database=str(db_path_empty), read_only=True)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM files")
    count = cursor.fetchone()[0]
    conn.close()
    assert count == 0, f"Expected 0 files in metadata after empty scan, found {count}"
    # No need to clean up DB, tmp_path handles it

    # --- Test 2: Scan Mixed Directory (with empty subdir) ---
    db_path_mixed = tmp_path / "mixed_scan.db" # Use a different DB path
    cmd_mixed = [
        sys.executable, "-m", "storage_hygiene.main",
        "--config", str(config_path), "--db-path", str(db_path_mixed), "--dry-run",
        str(scan_dir_mixed) # Target mixed directory
    ]

    print(f"\n--- Running Scan on Mixed Directory: {scan_dir_mixed} ---")
    result_mixed = subprocess.run(cmd_mixed, capture_output=True, text=True, cwd=PROJECT_ROOT, env=env)
    print("STDOUT (Mixed):\n", result_mixed.stdout)
    print("STDERR (Mixed):\n", result_mixed.stderr)

    assert result_mixed.returncode == 0, "Script failed on mixed directory scan"
    assert f"Scanning {scan_dir_mixed}..." in result_mixed.stderr
    assert "Scanning phase complete." in result_mixed.stderr
    # Analysis should find 0 actions based on default config and these unique files
    assert "Analysis complete. Found 0 potential actions." in result_mixed.stderr
    assert "Executing actions..." not in result_mixed.stderr

    # Check DB - should contain the 2 files found (ignores empty subdir)
    assert db_path_mixed.exists()
    conn = duckdb.connect(database=str(db_path_mixed), read_only=True)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM files")
    count = cursor.fetchone()[0]
    conn.close()
    assert count == 2, f"Expected 2 files in metadata after mixed scan, found {count}"
# Check that the empty subdirectory itself was NOT added
    conn = duckdb.connect(database=str(db_path_mixed), read_only=True) # Reconnect briefly
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM files WHERE path = ?", (str(scan_dir_mixed / "empty_subdir").replace('\\', '/'),)) # Normalize path for query
    empty_subdir_count = cursor.fetchone()[0]
    conn.close()
    assert empty_subdir_count == 0, f"Empty subdirectory '{scan_dir_mixed / 'empty_subdir'}' should not be in the database"

    assert not any(staging_dir.iterdir()), "Staging directory should be empty in dry run" # Keep this check too
def test_main_workflow_bad_staging_dir(setup_test_environment, capsys, tmp_path):
    """Tests error handling when staging directory is invalid or uncreatable."""
    scan_dir, staging_dir_fixture, db_path, config_path = setup_test_environment

    # --- Modify config to point to an invalid staging path ---
    # Point to an existing file path instead of a directory
    invalid_staging_path_file = tmp_path / "i_am_a_file.txt"
    invalid_staging_path_file.touch() # Create the file

    with open(config_path, 'r') as f:
        config_data = yaml.safe_load(f)
    config_data['action_executor']['staging_dir'] = str(invalid_staging_path_file) # Point config to the file
    with open(config_path, 'w') as f:
        yaml.dump(config_data, f)
    # --- End config modification ---

    # Command to run the main script (non-dry run to trigger action executor init/error)
    cmd = [
        sys.executable,
        "-m", "storage_hygiene.main",
        "--config", str(config_path),
        "--db-path", str(db_path),
        # No --dry-run, need ActionExecutor to try using the path
        str(scan_dir)
    ]

    # Environment setup
    env = os.environ.copy()
    python_path = env.get('PYTHONPATH', '')
    src_path_str = str(SRC_DIR)
    if src_path_str not in python_path.split(os.pathsep):
        env['PYTHONPATH'] = f"{src_path_str}{os.pathsep}{python_path}" if python_path else src_path_str

    # Execute the script
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT, env=env)

    # Print stdout/stderr for debugging
    print("STDOUT:\n", result.stdout)
    print("STDERR:\n", result.stderr)

    # Assertions
    assert result.returncode != 0, "Script should exit with non-zero code for invalid staging dir"

    # Check stderr for specific error messages related to the staging directory
    # The error originates from os.makedirs when trying to create a subdir inside the file path
    assert "FileNotFoundError: [WinError 3]" in result.stderr or \
           "ERROR - Error during action execution: [WinError 3]" in result.stderr, \
           "Expected FileNotFoundError or action execution error message not found in stderr"

    # Check that it didn't proceed fully to action execution if error happens early
    # It might get past analysis, but should fail before/during action execution.
    assert "Action execution complete." not in result.stderr
def test_main_workflow_only_old_files_rule(setup_test_environment, capsys):
    """Tests the main workflow with only the 'old_files' rule enabled."""
    scan_dir, staging_dir, db_path, config_path = setup_test_environment

    # --- Modify the config file ---
    with open(config_path, 'r') as f:
        config_data = yaml.safe_load(f)

    # Disable duplicate and large file rules
    config_data['analysis']['rules']['duplicate_files']['enabled'] = False
    config_data['analysis']['rules']['large_files']['enabled'] = False
    config_data['analysis']['rules']['old_files']['enabled'] = True # Ensure it's enabled

    with open(config_path, 'w') as f:
        yaml.dump(config_data, f)
    # --- End config modification ---

    # Command to run the main script (dry run is sufficient here)
    cmd = [
        sys.executable,
        "-m", "storage_hygiene.main",
        "--config", str(config_path),
        "--db-path", str(db_path),
        "--dry-run",
        str(scan_dir)
    ]

    # Environment setup
    env = os.environ.copy()
    python_path = env.get('PYTHONPATH', '')
    src_path_str = str(SRC_DIR)
    if src_path_str not in python_path.split(os.pathsep):
        env['PYTHONPATH'] = f"{src_path_str}{os.pathsep}{python_path}" if python_path else src_path_str

    # Execute the script
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT, env=env)

    # Print stdout/stderr for debugging
    print("STDOUT:\n", result.stdout)
    print("STDERR:\n", result.stderr)

    # Assertions
    assert result.returncode == 0, f"Script exited with error code {result.returncode}"

    # Check logs for key workflow steps
    assert "Starting Storage Hygiene System..." in result.stderr
    assert f"Loading configuration from: {config_path}" in result.stderr
    assert "Dry run mode enabled via CLI." in result.stderr
    assert "Initializing analysis engine..." in result.stderr
    assert "Running analysis..." in result.stderr

    # Verify analysis summary reflects only the old_files rule
    assert "Analysis complete. Found 1 potential actions." in result.stderr
    assert "- stage_duplicate:" not in result.stderr # Should not be present
    assert "- review_large:" not in result.stderr   # Should not be present
    assert "- review_old: 1 files" in result.stderr # Only old file action

    # Verify action execution reflects only the old file action
    assert "Executing actions... (Dry Run: True)" in result.stderr
    assert "Staging duplicate:" not in result.stdout # Should not be present
    assert "Staging large file:" not in result.stdout # Should not be present
    assert "Staging old file:" in result.stdout   # Only old file action
    assert "Action execution complete." in result.stderr
    assert "Storage Hygiene System finished successfully." in result.stderr

    # Check that staging directory is empty (dry run)
    assert not any(staging_dir.iterdir()), "Staging directory should be empty in dry run"
def test_main_workflow_large_file_threshold_variation(setup_test_environment, capsys):
    """Tests the large_files rule with a different min_size_mb threshold."""
    scan_dir, staging_dir, db_path, config_path = setup_test_environment

    # --- Modify the config file ---
    with open(config_path, 'r') as f:
        config_data = yaml.safe_load(f)

    # Change large file threshold to 5MB (fixture creates a 15MB file)
    config_data['analysis']['rules']['large_files']['enabled'] = True
    config_data['analysis']['rules']['large_files']['min_size_mb'] = 5
    # Disable other rules for isolation
    config_data['analysis']['rules']['duplicate_files']['enabled'] = False
    config_data['analysis']['rules']['old_files']['enabled'] = False

    with open(config_path, 'w') as f:
        yaml.dump(config_data, f)
    # --- End config modification ---

    # Command to run the main script (dry run is sufficient)
    cmd = [
        sys.executable,
        "-m", "storage_hygiene.main",
        "--config", str(config_path),
        "--db-path", str(db_path),
        "--dry-run",
        str(scan_dir)
    ]

    # Environment setup
    env = os.environ.copy()
    python_path = env.get('PYTHONPATH', '')
    src_path_str = str(SRC_DIR)
    if src_path_str not in python_path.split(os.pathsep):
        env['PYTHONPATH'] = f"{src_path_str}{os.pathsep}{python_path}" if python_path else src_path_str

    # Execute the script
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT, env=env)

    # Print stdout/stderr for debugging
    print("STDOUT:\n", result.stdout)
    print("STDERR:\n", result.stderr)

    # Assertions
    assert result.returncode == 0, f"Script exited with error code {result.returncode}"

    # Check logs for key workflow steps
    assert "Starting Storage Hygiene System..." in result.stderr
    assert f"Loading configuration from: {config_path}" in result.stderr
    assert "Dry run mode enabled via CLI." in result.stderr
    assert "Initializing analysis engine..." in result.stderr
    assert "Running analysis..." in result.stderr

    # Verify analysis summary reflects only the large_files rule with the 15MB file
    assert "Analysis complete. Found 1 potential actions." in result.stderr
    assert "- stage_duplicate:" not in result.stderr # Should not be present
    assert "- review_large: 1 files" in result.stderr   # Only large file action
    assert "- review_old:" not in result.stderr     # Should not be present

    # Verify action execution reflects only the large file action
    assert "Executing actions... (Dry Run: True)" in result.stderr
    assert "Staging duplicate:" not in result.stdout # Should not be present
    assert "Staging large file:" in result.stdout   # Only large file action
    assert "Staging old file:" not in result.stdout   # Should not be present
    assert "Action execution complete." in result.stderr
    assert "Storage Hygiene System finished successfully." in result.stderr

    # Check that staging directory is empty (dry run)
    assert not any(staging_dir.iterdir()), "Staging directory should be empty in dry run"
def test_main_workflow_different_staging_path(setup_test_environment, capsys, tmp_path):
    """Tests that files are staged to a different path specified in the config."""
    scan_dir, staging_dir_fixture, db_path, config_path = setup_test_environment

    # --- Create alternative staging path and modify config ---
    alt_staging_dir = tmp_path / "alternative_staging"
    alt_staging_dir.mkdir() # Create the alternative directory

    with open(config_path, 'r') as f:
        config_data = yaml.safe_load(f)
    config_data['action_executor']['staging_dir'] = str(alt_staging_dir) # Point config to alt path
    with open(config_path, 'w') as f:
        yaml.dump(config_data, f)
    # --- End config modification ---

    # Expected staging subdirectories within the *alternative* path
    alt_duplicate_stage_dir = alt_staging_dir / "duplicates"
    alt_large_stage_dir = alt_staging_dir / "large_files"
    alt_old_stage_dir = alt_staging_dir / "old_files"

    # Original file paths (from fixture)
    original_dup_src = scan_dir / "subdir" / "file2.txt"
    original_large_src = scan_dir / "large_file.bin"
    original_old_src = scan_dir / "old_file.log"

    # Expected destination paths within the *alternative* staging dir
    dup_content = b"duplicate_content"
    dup_hash = hashlib.sha256(dup_content).hexdigest()
    expected_alt_dup_dest = alt_duplicate_stage_dir / dup_hash[:2] / dup_hash / original_dup_src.name
    expected_alt_large_dest = alt_large_stage_dir / original_large_src.name
    expected_alt_old_dest = alt_old_stage_dir / original_old_src.name

    # Command to run the main script (NO --dry-run)
    cmd = [
        sys.executable,
        "-m", "storage_hygiene.main",
        "--config", str(config_path), # Use the modified config
        "--db-path", str(db_path),
        str(scan_dir)
    ]

    # Environment setup
    env = os.environ.copy()
    python_path = env.get('PYTHONPATH', '')
    src_path_str = str(SRC_DIR)
    if src_path_str not in python_path.split(os.pathsep):
        env['PYTHONPATH'] = f"{src_path_str}{os.pathsep}{python_path}" if python_path else src_path_str

    # Execute the script
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT, env=env)

    # Print stdout/stderr for debugging
    print("STDOUT:\n", result.stdout)
    print("STDERR:\n", result.stderr)

    # Assertions
    assert result.returncode == 0, f"Script exited with error code {result.returncode}"

    # Check file system for actual movement to *alternative* staging dir
    assert not original_dup_src.exists(), "Original duplicate file should not exist"
    assert not original_large_src.exists(), "Original large file should not exist"
    assert not original_old_src.exists(), "Original old file should not exist"

    assert expected_alt_dup_dest.exists(), f"Duplicate file should exist in alt staging: {expected_alt_dup_dest}"
    assert expected_alt_large_dest.exists(), f"Large file should exist in alt staging: {expected_alt_large_dest}"
    assert expected_alt_old_dest.exists(), f"Old file should exist in alt staging: {expected_alt_old_dest}"

    # Check that the original fixture staging dir remains empty
    assert not any(staging_dir_fixture.iterdir()), "Original fixture staging directory should be empty"

    # Check database content reflects the *alternative* staging paths
    assert db_path.exists()
    conn = duckdb.connect(database=str(db_path), read_only=True)
    cursor = conn.cursor()
    cursor.execute("SELECT path FROM files WHERE filename = ?", (original_dup_src.name,))
    dup_path_in_db = cursor.fetchone()[0]
    cursor.execute("SELECT path FROM files WHERE filename = ?", (original_large_src.name,))
    large_path_in_db = cursor.fetchone()[0]
    cursor.execute("SELECT path FROM files WHERE filename = ?", (original_old_src.name,))
    old_path_in_db = cursor.fetchone()[0]
    conn.close()

    assert Path(dup_path_in_db) == expected_alt_dup_dest, f"DB path for duplicate incorrect: {dup_path_in_db}"
    assert Path(large_path_in_db) == expected_alt_large_dest, f"DB path for large file incorrect: {large_path_in_db}"
    assert Path(old_path_in_db) == expected_alt_old_dest, f"DB path for old file incorrect: {old_path_in_db}"
def test_main_workflow_non_dry_run_multiple_matches(setup_test_environment, capsys, tmp_path):
    """Tests non-dry run with files matching multiple rules and multiple duplicates."""
    scan_dir, staging_dir, db_path, config_path = setup_test_environment

    # --- Create additional files for complex scenarios ---
    # Large AND Old file
    large_old_file_path = scan_dir / "large_and_old.zip"
    create_dummy_file(large_old_file_path, size_mb=20, mtime_days_ago=400)

    # Another duplicate of file1.txt
    another_dup_path = scan_dir / "another_subdir" / "file1_copy.txt"
    create_dummy_file(another_dup_path, content="duplicate_content")
    # --- End additional file creation ---

    # Expected staging subdirectories
    duplicate_stage_dir = staging_dir / "duplicates"
    large_stage_dir = staging_dir / "large_files"
    old_stage_dir = staging_dir / "old_files"

    # Original file paths (including new ones)
    original_dup_src1 = scan_dir / "subdir" / "file2.txt" # From fixture
    original_dup_src2 = another_dup_path
    original_large_src = scan_dir / "large_file.bin" # From fixture
    original_old_src = scan_dir / "old_file.log"   # From fixture
    original_large_old_src = large_old_file_path
    original_kept_dup_src = scan_dir / "file1.txt" # From fixture
    original_normal_src = scan_dir / "normal_file.txt" # From fixture

    # Expected destination paths
    dup_content = b"duplicate_content"
    dup_hash = hashlib.sha256(dup_content).hexdigest()
    # Duplicates (assuming file1.txt is kept, file2.txt and file1_copy.txt are staged)
    expected_dup_dest1 = duplicate_stage_dir / dup_hash[:2] / dup_hash / original_dup_src1.name
    expected_dup_dest2 = duplicate_stage_dir / dup_hash[:2] / dup_hash / original_dup_src2.name
    # Large file (from fixture)
    expected_large_dest = large_stage_dir / original_large_src.name
    # Old file (from fixture)
    expected_old_dest = old_stage_dir / original_old_src.name
    # Large AND Old file - Assuming 'large_files' takes precedence for staging destination
    expected_large_old_dest = large_stage_dir / original_large_old_src.name

    # Command to run the main script (NO --dry-run)
    cmd = [
        sys.executable, "-m", "storage_hygiene.main",
        "--config", str(config_path), "--db-path", str(db_path),
        str(scan_dir)
    ]

    # Environment setup
    env = os.environ.copy()
    python_path = env.get('PYTHONPATH', '')
    src_path_str = str(SRC_DIR)
    if src_path_str not in python_path.split(os.pathsep):
        env['PYTHONPATH'] = f"{src_path_str}{os.pathsep}{python_path}" if python_path else src_path_str

    # Execute the script
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT, env=env)

    # Print stdout/stderr for debugging
    print("STDOUT:\n", result.stdout)
    print("STDERR:\n", result.stderr)

    # Assertions
    assert result.returncode == 0, f"Script exited with error code {result.returncode}"

    # Check analysis summary (stderr) - Expect 2 duplicates, 2 large, 2 old -> 4 actions?
    # Duplicate rule identifies 2 files to stage.
    # Large rule identifies large_file.bin and large_and_old.zip.
    # Old rule identifies old_file.log and large_and_old.zip.
    # Assuming duplicate action takes precedence, and large takes precedence over old.
    # Actions: stage_duplicate (x2), review_large (x1 - large_file.bin), review_old (x1 - old_file.log)
    # The large_and_old file might be missed by review_large/review_old if duplicate runs first?
    # Let's refine this assertion after seeing the output. For now, check the key phases.
    assert "Analysis complete." in result.stderr # Check analysis ran
    assert "Executing actions... (Dry Run: False)" in result.stderr # Check execution ran

    # Check file system for actual movement
    assert not original_dup_src1.exists(), "Original duplicate 1 should not exist"
    assert not original_dup_src2.exists(), "Original duplicate 2 should not exist"
    assert not original_large_src.exists(), "Original large file should not exist"
    assert not original_old_src.exists(), "Original old file should not exist"
    assert not original_large_old_src.exists(), "Original large & old file should not exist" # Assuming it gets staged

    assert expected_dup_dest1.exists(), f"Duplicate 1 should exist in staging: {expected_dup_dest1}"
    assert expected_dup_dest2.exists(), f"Duplicate 2 should exist in staging: {expected_dup_dest2}"
    assert expected_large_dest.exists(), f"Large file should exist in staging: {expected_large_dest}"
    assert expected_old_dest.exists(), f"Old file should exist in staging: {expected_old_dest}"
    # Check where the large & old file ended up (assuming large precedence)
    assert expected_large_old_dest.exists(), f"Large & old file should exist in large staging: {expected_large_old_dest}"
    assert not (old_stage_dir / original_large_old_src.name).exists(), "Large & old file should NOT be in old staging"

    # Files that should remain untouched
    assert original_kept_dup_src.exists(), "Kept duplicate file should still exist"
    assert original_normal_src.exists(), "Normal file should still exist"

    # Check database content reflects the correct final paths
    assert db_path.exists()
    conn = duckdb.connect(database=str(db_path), read_only=True)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM files")
    # Expected count: 1 kept dup + 1 normal + 2 staged dups + 1 staged large + 1 staged old + 1 staged large/old = 7
    count = cursor.fetchone()[0]
    assert count == 7, f"Expected 7 files in metadata, found {count}"

    # Verify paths in DB point to the new staging locations
    cursor.execute("SELECT path FROM files WHERE filename = ?", (original_dup_src1.name,))
    assert Path(cursor.fetchone()[0]) == expected_dup_dest1
    cursor.execute("SELECT path FROM files WHERE filename = ?", (original_dup_src2.name,))
    assert Path(cursor.fetchone()[0]) == expected_dup_dest2
    cursor.execute("SELECT path FROM files WHERE filename = ?", (original_large_src.name,))
    assert Path(cursor.fetchone()[0]) == expected_large_dest
    cursor.execute("SELECT path FROM files WHERE filename = ?", (original_old_src.name,))
    assert Path(cursor.fetchone()[0]) == expected_old_dest
    cursor.execute("SELECT path FROM files WHERE filename = ?", (original_large_old_src.name,))
    assert Path(cursor.fetchone()[0]) == expected_large_old_dest # Check it points to large staging

    # Verify paths of untouched files remain correct
    cursor.execute("SELECT path FROM files WHERE filename = ?", (original_kept_dup_src.name,))
    assert Path(cursor.fetchone()[0]) == original_kept_dup_src.resolve()
    cursor.execute("SELECT path FROM files WHERE filename = ?", (original_normal_src.name,))
    assert Path(cursor.fetchone()[0]) == original_normal_src.resolve()

    conn.close()
def test_main_workflow_staging_permission_error(setup_test_environment, capsys, mocker):
    """Tests error handling when a PermissionError occurs during staging."""
    scan_dir, staging_dir, db_path, config_path = setup_test_environment

    # File that will trigger the error (any file subject to an action)
    target_file_path = scan_dir / "subdir" / "file2.txt" # Duplicate file

    # Mock shutil.move to raise PermissionError - This will now work as main is called directly
    mock_move = mocker.patch('shutil.move', side_effect=PermissionError("Test permission denied"))

    # Simulate command-line arguments for direct main() call
    test_argv = [
        "storage_hygiene/main.py", # Script name (sys.argv[0])
        "--config", str(config_path),
        "--db-path", str(db_path),
        str(scan_dir) # Target directory
        # No --dry-run
    ]
    mocker.patch.object(sys, 'argv', test_argv)

    # Import main function here to avoid potential global state issues if imported at top
    from storage_hygiene.main import main as main_function

    # Execute the main function directly and expect SystemExit
    with pytest.raises(SystemExit) as excinfo:
        main_function()

    # Assertions
    assert excinfo.value.code != 0, "Script should exit with non-zero code on critical staging error"

    # Capture and check stdout/stderr
    captured = capsys.readouterr()
    print("STDOUT:\n", captured.out)
    print("STDERR:\n", captured.err)

    # Check that shutil.move was called (or attempted)
    mock_move.assert_called()

    # Check stdout (since logging is directed there) for the critical error message
    # Note: The exact message might depend on where the logger catches it first
    assert "Critical OS error during action execution: Test permission denied" in captured.out or \
           "Critical error during action stage_duplicate" in captured.out, \
           "Expected permission error message not found in stdout" # Updated check location

    # Check that the original file still exists because the move failed
    assert target_file_path.exists(), "Original file should still exist after failed move"

    # Check that the database path was NOT updated for the failed file
    conn = duckdb.connect(database=str(db_path), read_only=True)
    cursor = conn.cursor()
    # Use normalized path for lookup as stored by Scanner
    normalized_target_path = os.path.normcase(str(target_file_path.resolve()))
    cursor.execute("SELECT path FROM files WHERE path = ?", (normalized_target_path,))
    path_in_db = cursor.fetchone()
    conn.close()
    assert path_in_db is not None, "Record for the file should still exist in DB"
    assert Path(path_in_db[0]) == target_file_path.resolve(), "DB path should not have been updated for the failed move"
def test_main_workflow_multiple_targets(setup_test_environment, capsys, tmp_path):
    """Tests scanning multiple target directories provided via CLI."""
    scan_dir_fixture, staging_dir, db_path, config_path = setup_test_environment

    # --- Create additional separate scan directories ---
    scan_dir_1 = tmp_path / "multi_scan_1"
    scan_dir_2 = tmp_path / "multi_scan_2"
    scan_dir_1.mkdir()
    scan_dir_2.mkdir()
    file_c_path = scan_dir_1 / "file_c.log"
    file_d_path = scan_dir_2 / "subdir" / "file_d.tmp"
    create_dummy_file(file_c_path, content="unique content c")
    create_dummy_file(file_d_path, content="unique content d")
    # --- End additional setup ---

    # Command to run the main script targeting both directories
    cmd = [
        sys.executable, "-m", "storage_hygiene.main",
        "--config", str(config_path),
        "--db-path", str(db_path),
        "--dry-run", # Dry run is fine, just checking scan
        str(scan_dir_1), # First target
        str(scan_dir_2)  # Second target
    ]

    # Environment setup
    env = os.environ.copy()
    python_path = env.get('PYTHONPATH', '')
    src_path_str = str(SRC_DIR)
    if src_path_str not in python_path.split(os.pathsep):
        env['PYTHONPATH'] = f"{src_path_str}{os.pathsep}{python_path}" if python_path else src_path_str

    # Execute the script
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT, env=env)

    # Print stdout/stderr for debugging
    print("STDOUT:\n", result.stdout)
    print("STDERR:\n", result.stderr)

    # Assertions
    assert result.returncode == 0, f"Script exited with error code {result.returncode}"

    # Check logs confirm both directories were targeted
    assert f"Scanning target directories: {scan_dir_1}, {scan_dir_2}" in result.stderr or \
           f"Scanning target directories: {scan_dir_2}, {scan_dir_1}" in result.stderr # Order might vary
    assert f"Scanning {scan_dir_1}..." in result.stderr
    assert f"Scanning {scan_dir_2}..." in result.stderr
    assert "Scanning phase complete." in result.stderr

    # Check database content - should contain files from both scans
    assert db_path.exists()
    conn = duckdb.connect(database=str(db_path), read_only=True)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM files")
    count = cursor.fetchone()[0]
    # Expecting 2 files from this test + 5 from the fixture setup = 7?
    # Let's check specifically for the new files.
    cursor.execute("SELECT path FROM files WHERE filename = ?", (file_c_path.name,))
    path_c = cursor.fetchone()
    cursor.execute("SELECT path FROM files WHERE filename = ?", (file_d_path.name,))
    path_d = cursor.fetchone()
    conn.close()

    # The fixture files might also be scanned if scan_dir_fixture was passed implicitly?
    # Let's adjust the test to use a clean DB path to isolate the multi-target scan.
    # RETHINK: The fixture setup uses tmp_path, so the DB should be clean per test run.
    # The test only scans scan_dir_1 and scan_dir_2, which contain 1 file each.
    assert count == 2, f"Expected 2 files (1 from each target dir) in metadata, found {count}"
    assert path_c is not None, f"File '{file_c_path.name}' not found in DB"
    assert path_d is not None, f"File '{file_d_path.name}' not found in DB"
    assert Path(path_c[0]) == file_c_path.resolve()
    assert Path(path_d[0]) == file_d_path.resolve()
def test_main_workflow_non_dry_run_alt_db(setup_test_environment, capsys, tmp_path):
    """Tests non-dry run using an alternative DB path specified via CLI."""
    scan_dir, staging_dir, db_path_fixture, config_path = setup_test_environment

    # --- Define alternative DB path ---
    alt_db_path = tmp_path / "alternative_run.db"
    # --- End alternative setup ---

    # Expected staging paths (same as non-dry run test, just verifying DB interaction)
    duplicate_stage_dir = staging_dir / "duplicates"
    large_stage_dir = staging_dir / "large_files"
    old_stage_dir = staging_dir / "old_files"
    original_dup_src = scan_dir / "subdir" / "file2.txt"
    original_large_src = scan_dir / "large_file.bin"
    original_old_src = scan_dir / "old_file.log"
    dup_content = b"duplicate_content"
    dup_hash = hashlib.sha256(dup_content).hexdigest()
    expected_dup_dest = duplicate_stage_dir / dup_hash[:2] / dup_hash / original_dup_src.name
    expected_large_dest = large_stage_dir / original_large_src.name
    expected_old_dest = old_stage_dir / original_old_src.name

    # Command using alternative DB path via CLI argument (NO --dry-run)
    cmd = [
        sys.executable, "-m", "storage_hygiene.main",
        "--config", str(config_path),
        "--db-path", str(alt_db_path), # Use alternative DB path
        str(scan_dir)
    ]

    # Environment setup
    env = os.environ.copy()
    python_path = env.get('PYTHONPATH', '')
    src_path_str = str(SRC_DIR)
    if src_path_str not in python_path.split(os.pathsep):
        env['PYTHONPATH'] = f"{src_path_str}{os.pathsep}{python_path}" if python_path else src_path_str

    # Execute the script
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT, env=env)

    # Print stdout/stderr for debugging
    print("STDOUT:\n", result.stdout)
    print("STDERR:\n", result.stderr)

    # Assertions
    assert result.returncode == 0, f"Script exited with error code {result.returncode}"

    # Verify logs show the *alternative* DB path being used
    assert f"Initializing metadata store at: {alt_db_path}" in result.stderr, "Alternative DB path not found in logs"

    # Verify the alternative DB file was created and contains correct data
    assert alt_db_path.exists(), "Alternative DB file was not created"
    assert not db_path_fixture.exists(), "Fixture DB file should not have been created"

    conn = duckdb.connect(database=str(alt_db_path), read_only=True)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM files")
    count = cursor.fetchone()[0]
    assert count == 5, f"Expected 5 files in alternative DB, found {count}"
    # Verify paths in DB point to the new staging locations
    cursor.execute("SELECT path FROM files WHERE filename = ?", (original_dup_src.name,))
    assert Path(cursor.fetchone()[0]) == expected_dup_dest
    cursor.execute("SELECT path FROM files WHERE filename = ?", (original_large_src.name,))
    assert Path(cursor.fetchone()[0]) == expected_large_dest
    cursor.execute("SELECT path FROM files WHERE filename = ?", (original_old_src.name,))
    assert Path(cursor.fetchone()[0]) == expected_old_dest
    conn.close()

    # Verify files were actually moved (redundant check, but good for integration)
    assert not original_dup_src.exists()
    assert not original_large_src.exists()
    assert not original_old_src.exists()
    assert expected_dup_dest.exists()
    assert expected_large_dest.exists()
    assert expected_old_dest.exists()