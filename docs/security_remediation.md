# Security remediation report

## Incident

The public repository shipped a hardcoded MySQL credential in the
application source (project_helper5.py, `connect_to_database()`): host
`127.0.0.1`, user `root`, a real-looking root password, database `farmer2`.
The value is deliberately not reproduced in this report. Exposure window:
2026-02-02 (initial public upload) until remediation.

## Classification

Treat the credential as **compromised**. It protected a localhost MySQL
instance, which limits blast radius, but any credential published for months
must be rotated and never reused.

## Remediation performed in this repository

1. **Removed the credential from the active application code.** The new
   `src/plant_app/database/connection.py` reads all connection parameters
   from environment variables (`DB_*`) with no default password.
2. **`.env.example` added** documenting every optional variable; `.env` is
   git-ignored; `.gitignore` added covering `.env`, secrets, demo databases,
   and OS/IDE noise.
3. **Regression guard**: `tests/smoke/test_app_smoke.py::test_no_hardcoded_credentials`
   scans all non-legacy Python sources for hardcoded passwords and fails the
   suite if one reappears; the CI secret scan does the same for
   password/api-key/secret/token literals.
4. **Placeholder keys surfaced honestly.** The legacy placeholder OpenAI and
   SerpAPI keys were hardcoded strings; both services now require real keys
   from the environment and degrade gracefully otherwise.
5. **Legacy sources quarantined, not deleted.** The original files are kept
   verbatim as `docs/legacy_project_helper5.py`,
   `docs/legacy_pepper_prediction.py`, `docs/legacy_requirements.txt` so the
   historical record is auditable; they are excluded from the secret-scan
   guards and marked as containing the old credential.

## Owner actions required (cannot be done from this workspace)

1. **Rotate the exposed MySQL root password now.** Change it on every system
   where it was used; do not reuse it anywhere.
2. **History purge decision.** The credential remains in Git history
   (commit `4d87028` "Initial upload (Clean)" and its descendants until this
   fix). Because the published history is only two commits deep, a clean
   purge is cheap: after backing up (branch `backup/pre-rehab-4d87028`
   already exists locally), rewrite the initial commit to contain the
   sanitized files and force-push, then confirm via GitHub support that
   orphaned commit views are purged if the repo had forks/watchers.
   Requirement: owner approval before any force-push (per the audit brief).
   Alternative, zero-risk option: rotate the password and leave history as
   is, documenting that the old credential is dead.
3. **GitHub UI**: if the repository is archived (it was at audit time), it
   must be unarchived before any of this can be pushed.

## Secret-scan evidence

Static pattern scan across all commits, tracked files, `.idea` configs, and
the extracted text of the bundled PDF found credential-shaped strings only
in `project_helper5.py` (the incident above) and no API keys, tokens, or
passwords elsewhere.
