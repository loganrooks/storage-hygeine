# tests/integration/test_main_workflow.py
import pytest
import subprocess
import sys
import os
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