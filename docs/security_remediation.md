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
    under `docs/legacy_*` with exactly one content change: the rotated
    credential value was redacted in commit `205a10c`; everything else is
    verbatim so the historical record is auditable. They are excluded from
    the secret-scan guards and labeled as containing the redacted marker.

## Rotation status (updated 2026-11-27)

1. **Rotated and verified.** The exposed root password was rotated on
   2026-11-27 on the local MySQL81 service via authorized access, and the
   old credential was verified to no longer authenticate (authentication
   refused after rotation). The replacement password is stored only in the
   git-ignored `.env` of this repository.
2. **Local administrative recovery pending.** The replacement password was
   lost during cleanup, so regaining local root access requires running
   `_audit/reports/recovery2.py` from an elevated shell (restarts MySQL81
   with `--skip-grant-tables`, resets root, restarts the service, verifies
   both transitions). Until this runs, MySQL mode is unconfigured; the app
   default is SQLite and works without it.
3. **History purge decision pending.** The original credential remains
   reachable in Git history at commit `4d87028` and its descendants. It is
   verifiably dead. A filter-repo cleanup plus force-with-lease push remains
   available but awaits a separate documented owner decision; cached views
   and prior clones may persist regardless, and GitHub Support intervention
   would be needed for orphaned-commit purge.
4. **Unarchive: done.** The repository was unarchived and the rehabilitation
   was published on `main` (PRs #1-#3).

## Secret-scan evidence

Static pattern scan across all commits, tracked files, `.idea` configs, and
the extracted text of the bundled PDF found credential-shaped strings only
in `project_helper5.py` (the incident above) and no API keys, tokens, or
passwords elsewhere.
