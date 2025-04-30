import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone, timedelta

# Assume AnalysisEngine will be in src.storage_hygiene.analysis_engine
# We expect an ImportError initially
try:
    from src.storage_hygiene.analysis_engine import AnalysisEngine
except ImportError:
    AnalysisEngine = None # Allow tests to be defined even if class doesn't exist yet

# Mock dependencies
@pytest.fixture
def mock_config_manager():
    """Provides a mock ConfigManager."""
    return MagicMock()

@pytest.fixture
def mock_metadata_store():
    """Provides a mock MetadataStore."""
    return MagicMock()

def test_analysis_engine_initialization(mock_config_manager, mock_metadata_store):
    """
    Test TDD Anchor: [AE_Init]
    Test that AnalysisEngine can be initialized with dependencies.
    """
    if AnalysisEngine is None:
        pytest.fail("AnalysisEngine class not found. Implement the class.")

    engine = AnalysisEngine(mock_config_manager, mock_metadata_store)
    assert engine.config_manager is mock_config_manager
def test_analysis_engine_loads_rules_from_config(mock_config_manager, mock_metadata_store):
    """
    Test TDD Anchor: [AE_LoadRules]
    Test that AnalysisEngine loads rules from ConfigManager during init.
    """
    if AnalysisEngine is None:
        pytest.fail("AnalysisEngine class not found.")

    expected_rules = {
        'duplicate_files': {'enabled': True},
        'large_files': {'enabled': True, 'min_size_mb': 100},
        'old_files': {'enabled': False, 'max_days': 365}
    }
    mock_config_manager.get.return_value = expected_rules

    engine = AnalysisEngine(mock_config_manager, mock_metadata_store)

    # Verify that config_manager.get was called correctly
    mock_config_manager.get.assert_called_once_with('analysis.rules', {})

    # Verify that the rules are loaded correctly
    assert engine.rules == expected_rules
def test_analyze_identifies_duplicate_files(mock_config_manager, mock_metadata_store):
    """
    Test TDD Anchor: [AE_Analyze_Duplicates]
    Test that the analyze method correctly identifies duplicate files based on hash
    and generates 'stage_duplicate' actions.
    """
    if AnalysisEngine is None:
        pytest.fail("AnalysisEngine class not found.")

    # --- Arrange ---
    # Configure rules: Enable duplicate detection
    rules = {
        'duplicate_files': {'enabled': True},
        'large_files': {'enabled': False}, # Disable other rules for isolation
        'old_files': {'enabled': False}
    }
    mock_config_manager.get.return_value = rules

    # Configure metadata store mock to return duplicate files
    # Grouped by hash, excluding hashes with only one file
    mock_metadata_store.query_files.return_value = [
        # Duplicate set 1 (hash123) - Keep file1.txt, stage file3.txt
        {'path': '/path/to/file1.txt', 'hash': 'hash123', 'size': 100, 'last_modified': datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)},
        {'path': '/path/to/subdir/file3.txt', 'hash': 'hash123', 'size': 100, 'last_modified': datetime(2024, 1, 1, 11, 0, 0, tzinfo=timezone.utc)},
        # Unique file (hash456) - Should be ignored
        {'path': '/path/to/file2.txt', 'hash': 'hash456', 'size': 200, 'last_modified': datetime(2024, 1, 2, 10, 0, 0, tzinfo=timezone.utc)},
        # Duplicate set 2 (hash789) - Keep file4.bin, stage file5.bin
        {'path': '/another/path/file4.bin', 'hash': 'hash789', 'size': 500, 'last_modified': datetime(2023, 12, 1, 0, 0, 0, tzinfo=timezone.utc)},
        {'path': '/yet/another/file5.bin', 'hash': 'hash789', 'size': 500, 'last_modified': datetime(2023, 12, 15, 0, 0, 0, tzinfo=timezone.utc)},
    ]
    # Mock the specific query used by the duplicate rule
    mock_metadata_store.get_duplicates.return_value = {
        'hash123': [
            {'path': '/path/to/file1.txt', 'hash': 'hash123', 'size': 100, 'last_modified': datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)},
            {'path': '/path/to/subdir/file3.txt', 'hash': 'hash123', 'size': 100, 'last_modified': datetime(2024, 1, 1, 11, 0, 0, tzinfo=timezone.utc)},
        ],
        'hash789': [
            {'path': '/another/path/file4.bin', 'hash': 'hash789', 'size': 500, 'last_modified': datetime(2023, 12, 1, 0, 0, 0, tzinfo=timezone.utc)},
            {'path': '/yet/another/file5.bin', 'hash': 'hash789', 'size': 500, 'last_modified': datetime(2023, 12, 15, 0, 0, 0, tzinfo=timezone.utc)},
        ]
    }


    engine = AnalysisEngine(mock_config_manager, mock_metadata_store)
    engine.rules = rules # Explicitly set rules after init for clarity in test

    # --- Act ---
    action_candidates = engine.analyze()

    # --- Assert ---
    # Verify metadata store was queried correctly for duplicates
    mock_metadata_store.get_duplicates.assert_called_once()

    # Define expected actions (staging the newer file in each duplicate set)
    expected_actions = [
        {'action': 'stage_duplicate', 'path': '/path/to/subdir/file3.txt', 'hash': 'hash123', 'original_path': '/path/to/file1.txt', 'reason': 'Duplicate of /path/to/file1.txt'},
        {'action': 'stage_duplicate', 'path': '/yet/another/file5.bin', 'hash': 'hash789', 'original_path': '/another/path/file4.bin', 'reason': 'Duplicate of /another/path/file4.bin'},
    ]

    # Use a set comparison to ignore order
    assert len(action_candidates) == len(expected_actions)
    assert set(tuple(sorted(d.items())) for d in action_candidates) == set(tuple(sorted(d.items())) for d in expected_actions)
    assert engine.metadata_store is mock_metadata_store
def test_analyze_identifies_large_files(mock_config_manager, mock_metadata_store):
    """
    Test TDD Anchor: [AE_Analyze_Large]
    Test that the analyze method correctly identifies large files based on config
    and generates 'review_large' actions.
    """
    if AnalysisEngine is None:
        pytest.fail("AnalysisEngine class not found.")

    # --- Arrange ---
    min_size_mb = 50
    min_size_bytes = min_size_mb * 1024 * 1024
    rules = {
        'duplicate_files': {'enabled': False}, # Disable other rules
        'large_files': {'enabled': True, 'min_size_mb': min_size_mb},
        'old_files': {'enabled': False}
    }
    mock_config_manager.get.return_value = rules

    # Configure metadata store mock to return files of various sizes
    mock_metadata_store.query_files.return_value = [
        {'path': '/path/to/small_file.txt', 'hash': 'hash1', 'size': 10 * 1024 * 1024, 'last_modified': datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)},
        {'path': '/path/to/large_video.mp4', 'hash': 'hash2', 'size': 150 * 1024 * 1024, 'last_modified': datetime(2024, 1, 2, 11, 0, 0, tzinfo=timezone.utc)},
        {'path': '/path/to/exact_size_file.iso', 'hash': 'hash3', 'size': min_size_bytes, 'last_modified': datetime(2024, 1, 3, 12, 0, 0, tzinfo=timezone.utc)}, # Exactly at threshold
        {'path': '/path/to/another_large.zip', 'hash': 'hash4', 'size': 60 * 1024 * 1024, 'last_modified': datetime(2024, 1, 4, 13, 0, 0, tzinfo=timezone.utc)}, # Slightly above threshold
    ]
    # Mock get_duplicates to return empty if called (it shouldn't be)
    mock_metadata_store.get_duplicates.return_value = {}

    engine = AnalysisEngine(mock_config_manager, mock_metadata_store)
    engine.rules = rules # Explicitly set rules

    # --- Act ---
    action_candidates = engine.analyze()

    # --- Assert ---
    # Verify metadata store was queried correctly (expecting a query for all files)
    # We'll refine this assertion if a more specific query is implemented later
    mock_metadata_store.query_files.assert_called_once()
    # Ensure get_duplicates was NOT called as the rule is disabled
    mock_metadata_store.get_duplicates.assert_not_called()

    # Define expected actions (only files strictly larger than the threshold)
    expected_actions = [
        {'action': 'review_large', 'path': '/path/to/large_video.mp4', 'size': 150 * 1024 * 1024, 'reason': f'File size (150.0 MB) exceeds threshold ({min_size_mb} MB)'},
        {'action': 'review_large', 'path': '/path/to/another_large.zip', 'size': 60 * 1024 * 1024, 'reason': f'File size (60.0 MB) exceeds threshold ({min_size_mb} MB)'},
        # Note: The file exactly at the threshold is NOT included
    ]

    # Use a set comparison to ignore order
    assert len(action_candidates) == len(expected_actions)
    # Convert dicts to comparable tuples of sorted items
    action_candidates_set = set(tuple(sorted(d.items())) for d in action_candidates)
    expected_actions_set = set(tuple(sorted(d.items())) for d in expected_actions)
    assert action_candidates_set == expected_actions_set
def test_analyze_identifies_old_files(mock_config_manager, mock_metadata_store):
    """
    Test TDD Anchor: [AE_Analyze_Old]
    Test that the analyze method correctly identifies old files based on config
    and generates 'review_old' actions.
    """
    if AnalysisEngine is None:
        pytest.fail("AnalysisEngine class not found.")

    # --- Arrange ---
    max_days = 90
    now = datetime.now(timezone.utc)
    threshold_date = now - timedelta(days=max_days)

    rules = {
        'duplicate_files': {'enabled': False},
        'large_files': {'enabled': False},
        'old_files': {'enabled': True, 'max_days': max_days}
    }
    mock_config_manager.get.return_value = rules

    # Configure metadata store mock to return files with various modification dates
    mock_metadata_store.query_files.return_value = [
        {'path': '/path/to/recent_file.txt', 'hash': 'hash_r', 'size': 1024, 'last_modified': now - timedelta(days=30)},
        {'path': '/path/to/old_doc.pdf', 'hash': 'hash_o1', 'size': 2048, 'last_modified': now - timedelta(days=100)}, # Older than threshold
        {'path': '/path/to/very_old_archive.zip', 'hash': 'hash_o2', 'size': 512000, 'last_modified': now - timedelta(days=365)}, # Much older
        {'path': '/path/to/boundary_file.log', 'hash': 'hash_b', 'size': 4096, 'last_modified': threshold_date - timedelta(seconds=1)}, # Just past threshold
        {'path': '/path/to/not_old_file.py', 'hash': 'hash_n', 'size': 8192, 'last_modified': threshold_date + timedelta(days=1)}, # Newer than threshold
    ]
    # Mock get_duplicates to return empty if called (it shouldn't be)
    mock_metadata_store.get_duplicates.return_value = {}

    engine = AnalysisEngine(mock_config_manager, mock_metadata_store)
    engine.rules = rules # Explicitly set rules

    # --- Act ---
    action_candidates = engine.analyze()

    # --- Assert ---
    # Verify metadata store was queried correctly (expecting a query for all files)
    mock_metadata_store.query_files.assert_called_once()
    # Ensure get_duplicates was NOT called
    mock_metadata_store.get_duplicates.assert_not_called()

    # Define expected actions (only files older than the threshold date)
    expected_actions = [
        {'action': 'review_old', 'path': '/path/to/old_doc.pdf', 'last_modified': mock_metadata_store.query_files.return_value[1]['last_modified'], 'reason': f'File older than {max_days} days'},
        {'action': 'review_old', 'path': '/path/to/very_old_archive.zip', 'last_modified': mock_metadata_store.query_files.return_value[2]['last_modified'], 'reason': f'File older than {max_days} days'},
        {'action': 'review_old', 'path': '/path/to/boundary_file.log', 'last_modified': mock_metadata_store.query_files.return_value[3]['last_modified'], 'reason': f'File older than {max_days} days'},
    ]

    # Use a set comparison to ignore order
    assert len(action_candidates) == len(expected_actions)
    action_candidates_set = set(tuple(sorted(d.items())) for d in action_candidates)
    expected_actions_set = set(tuple(sorted(d.items())) for d in expected_actions)
    assert action_candidates_set == expected_actions_set