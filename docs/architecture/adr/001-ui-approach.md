# ADR-001: UI Approach (Revised)

**Date:** 2025-04-29
**Status:** Accepted (Revised based on user feedback)

## Context

The Storage Hygiene System requires a user interface to initiate scans, configure settings, display analysis results (lists of files categorized for action), allow users to review these suggestions, confirm actions, and monitor execution progress. The initial proposal included a Web UI, but user feedback indicated a preference for a simpler, CLI-focused approach.

## Decision

We will implement the user interface as **CLI-only**. Key interactions will be:
1.  **Initiation & Configuration:** Use CLI commands and arguments (e.g., `hygiene scan --path /mnt/data --rules large,old`, `hygiene config set rule.large.threshold 1GB`).
2.  **Reporting:** Output analysis results as formatted text tables (e.g., using `rich` or `tabulate`) or plain file lists directed to stdout or files (e.g., `hygiene report --category duplicates > duplicates.txt`).
3.  **Review:** Users will review the generated file lists/reports. For detailed inspection of specific files, users will use external tools (e.g., `vim duplicates.txt`, `xdg-open /path/to/suspicious/file.pdf`, `code /path/to/config.yaml`) based on the paths provided in the CLI output.
4.  **Confirmation:** Actions will be confirmed either via interactive prompts within the CLI (e.g., using `inquirerpy` or similar for yes/no confirmation on categories or individual items if needed) or by providing pre-approved lists/categories to the execution command (e.g., `hygiene execute --confirm-delete duplicates.txt`, `hygiene execute --confirm-action large --action move_trash`).
5.  **Progress:** Display progress bars (e.g., using `tqdm` or `rich.progress`) and log messages to stderr/stdout during long-running operations (scan, analysis, execution).

## Rationale

*   **User Preference:** Directly addresses user feedback requesting a CLI-only interface for simplicity.
*   **Reduced Complexity:** Eliminates the need to develop and maintain a separate Web UI (frontend and backend server), significantly reducing development scope and dependencies.
*   **Leverages Existing Tools:** Users can leverage powerful existing tools (text editors, file managers, viewers) for detailed file inspection, which are often more feature-rich than custom previews within a dedicated UI.
*   **Scriptability:** A CLI interface is inherently scriptable, facilitating automation of hygiene tasks.
*   **Focus:** Allows development effort to concentrate entirely on the core backend logic, analysis algorithms, and execution reliability.

## Alternatives Considered

*   **Web Application UI (Local Server):** Original proposal, rejected based on user feedback preferring simplicity and avoiding a local web server requirement.
*   **Desktop Application (e.g., Electron, Tauri, PyQt):** Rejected due to cross-platform development complexity, larger distribution size, and user preference for CLI.
*   **TUI (Text-based User Interface, e.g., using `curses`, `prompt_toolkit`):** Considered as a middle ground, but rejected in favor of simpler CLI commands and leveraging external tools for review, reducing the complexity of building and maintaining a TUI layout. Standard CLI output is also more easily parsable/redirectable.

## Consequences

*   The user experience relies heavily on the clarity and usability of the CLI commands, arguments, and output formats. Good documentation and help messages are crucial.
*   Reviewing very large numbers of files might be less convenient than a dedicated GUI with sorting/filtering/preview capabilities, although outputting lists to files allows users to use external tools (`grep`, `awk`, spreadsheets) for analysis.
*   Requires users to be comfortable working with the command line and external tools for file inspection.
*   Interactive confirmation needs careful design to avoid accidental data loss (e.g., clear prompts, potentially requiring explicit flags for destructive operations).
*   Python libraries like `rich`, `tabulate`, `inquirerpy`, `tqdm`, and `argparse`/`click`/`typer` will be key dependencies for building the CLI.