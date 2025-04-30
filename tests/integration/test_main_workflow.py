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