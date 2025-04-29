# ADR-002: Credential Management

**Date:** 2025-04-29
**Status:** Proposed

## Context

The Storage Hygiene System needs to interact with cloud services (Microsoft OneDrive via Graph API, Google Drive API) and potentially AI services (Google Vertex AI). These interactions require sensitive API keys or credentials that must be stored and accessed securely. Hardcoding credentials or storing them in plain text configuration files is unacceptable due to security risks.

## Decision

We will use the native Operating System's secure credential store (OS Keychain) via the Python `keyring` library as the primary mechanism for storing and retrieving sensitive credentials (API keys, potentially OAuth tokens if needed later). The `Configuration Manager` component will be responsible for interacting with the `keyring` library.

## Rationale

*   **Security:** Leverages OS-level security mechanisms (Windows Credential Manager, macOS Keychain, Linux Secret Service/KWallet) designed for storing sensitive data. Avoids risks associated with plain text files or custom encryption schemes.
*   **Usability:** The `keyring` library provides a consistent, cross-platform Python API, abstracting away OS-specific differences. On first use, the application (via UI or CLI) can prompt the user for credentials, which are then securely stored by `keyring` for subsequent use without further prompts.
*   **Standard Practice:** Using the OS keychain is a standard and recommended practice for desktop applications handling sensitive user credentials or API keys.

## Alternatives Considered

*   **Environment Variables:** Rejected. While common for server applications, they are less secure on multi-user desktop systems (potentially visible in process lists) and inconvenient for users to manage persistently and securely.
*   **Encrypted Configuration File:** Rejected. Requires secure management of the encryption key itself (creating a chicken-and-egg problem) and relies on custom implementation, which is prone to security flaws.
*   **Cloud Secrets Manager (e.g., AWS Secrets Manager, GCP Secret Manager):** Rejected. Overkill for a local desktop application. Introduces unnecessary cloud dependency, potential costs, and complexity for managing secrets that only need to be accessed locally.
*   **Plain Text Configuration File:** Rejected. Fundamentally insecure.

## Consequences

*   Requires the `keyring` Python library as a dependency.
*   Requires appropriate backend support on Linux systems (e.g., `secret-service` or `kwallet` DBus services running). Installation instructions may need to guide users on setting this up if missing.
*   The `Configuration Manager` component needs logic to interact with `keyring` (`get_password`, `set_password`) and handle cases where credentials are not found (triggering user prompt).
*   User must grant permission on macOS/Linux when the application first tries to access/store a credential in the keychain.