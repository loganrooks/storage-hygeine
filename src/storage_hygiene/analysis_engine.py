from datetime import datetime, timezone, timedelta
class AnalysisEngine:
    """
    Analyzes file metadata based on configured rules to identify potential
    actions like identifying duplicates, large files, or old files.
    """
    def __init__(self, config_manager, metadata_store):
        """
        Initializes the AnalysisEngine.

        Args:
            config_manager: An instance of ConfigManager.
            metadata_store: An instance of MetadataStore.
        """
        self.config_manager = config_manager
        self.metadata_store = metadata_store
        self._load_rules()

    def _load_rules(self):
        """Loads analysis rules from the configuration manager."""
        self.rules = self.config_manager.get('analysis.rules', {})

    def analyze(self):
        """
        Performs the analysis based on loaded rules and metadata.

        Returns:
            list: A list of candidate action dictionaries.
        """
        action_candidates = []

        self._apply_duplicate_rule(action_candidates)
        self._apply_large_file_rule(action_candidates)
        self._apply_old_file_rule(action_candidates)

        return action_candidates

    def _apply_duplicate_rule(self, action_candidates):
        """Applies the duplicate file detection rule."""
        duplicate_rule = self.rules.get('duplicate_files', {})
        if not duplicate_rule.get('enabled', False):
            return # Rule disabled

        duplicate_sets = self.metadata_store.get_duplicates()
        for hash_value, files in duplicate_sets.items():
            if len(files) > 1:
                # Sort files to keep the oldest one (or by path as tie-breaker)
                files.sort(key=lambda x: (x['last_modified'], x['path']))
                original_file = files[0]
                for duplicate_file in files[1:]:
                    action_candidates.append({
                        'action': 'stage_duplicate',
                        'path': duplicate_file['path'],
                        'hash': hash_value,
                        'original_path': original_file['path'],
                        'reason': f"Duplicate of {original_file['path']}"
                    })

    def _apply_large_file_rule(self, action_candidates):
        """Applies the large file detection rule."""
        large_file_rule = self.rules.get('large_files', {})
        if not large_file_rule.get('enabled', False):
            return # Rule disabled

        min_size_mb = large_file_rule.get('min_size_mb')
        if min_size_mb is None:
            # Log a warning or handle missing config appropriately
            print("Warning: Large file rule enabled but min_size_mb not set.")
            return

        min_size_bytes = min_size_mb * 1024 * 1024

        # Query all files for simplicity now. Could optimize later if needed.
        all_files = self.metadata_store.query_files()

        for file_record in all_files:
            if file_record['size'] > min_size_bytes:
                size_mb = file_record['size'] / (1024 * 1024)
                action_candidates.append({
                    'action': 'review_large',
                    'path': file_record['path'],
                    'size': file_record['size'],
                    'reason': f'File size ({size_mb:.1f} MB) exceeds threshold ({min_size_mb} MB)'
                })
    def _apply_old_file_rule(self, action_candidates):
        """Applies the old file detection rule."""
        old_file_rule = self.rules.get('old_files', {})
        if not old_file_rule.get('enabled', False):
            return # Rule disabled

        max_days = old_file_rule.get('max_days')
        if max_days is None:
            print("Warning: Old file rule enabled but max_days not set.")
            return

        try:
            max_days_int = int(max_days)
            if max_days_int <= 0:
                print("Warning: Old file rule max_days must be a positive integer.")
                return
        except (ValueError, TypeError):
            print("Warning: Old file rule max_days must be a positive integer.")
            return

        now = datetime.now(timezone.utc)
        threshold_date = now - timedelta(days=max_days_int)

        # Query all files for simplicity now.
        all_files = self.metadata_store.query_files()

        for file_record in all_files:
            # Ensure last_modified is timezone-aware (assuming UTC from MetadataStore)
            last_modified = file_record.get('last_modified')
            if last_modified and last_modified.tzinfo is None:
                 # Attempt to make it timezone-aware, assuming UTC if naive
                 # This might need adjustment based on how MetadataStore stores dates
                 print(f"Warning: Naive datetime encountered for {file_record['path']}. Assuming UTC.")
                 last_modified = last_modified.replace(tzinfo=timezone.utc)

            if last_modified and last_modified < threshold_date:
                action_candidates.append({
                    'action': 'review_old',
                    'path': file_record['path'],
                    'last_modified': last_modified, # Store the actual datetime object
                    'reason': f'File older than {max_days_int} days'
                })
