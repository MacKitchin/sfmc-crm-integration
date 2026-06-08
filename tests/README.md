# Security guideline tests

`check_security_guidelines.py` mechanically verifies that the **Security & Secrets**
standards documented in `SKILL.md` are actually upheld by a repository's state. It is a
guardrail to catch the common ways a credential leaks into version control — not a
replacement for human review or GitHub secret scanning.

No third-party dependencies (Python 3.8+, just `git` on `PATH`).

## What it checks

Full audit (default):

- **gitignore-coverage** — `.gitignore` exists and lists the documented secret patterns
  (`.env`, `client_secret*`, `*.secret`, `*.token`, `*.pem`, `*.key`).
- **gitignore-effective** — `git check-ignore` confirms git actually ignores representative
  secret files.
- **no-secret-files** — no secret-bearing files are tracked (`.env`, `*.pem`, `*.key`,
  `credentials*`, `id_rsa*`, …); `*.example`/`*.sample`/`*.template` are allowed.
- **no-secret-values** — no real secret *values* in tracked text content. Obvious
  placeholders (`YOUR_SECRET`, `<...>`, `{{...}}`, `$VAR`, `os.environ[...]`, etc.) are
  allowed; non-credential config identifiers (Org ID, client ID, subdomain) are not flagged.
- **history-clean** — scans every unique text blob in git history for the same secret
  patterns (skip with `--no-history`).
- **docs-present** — `SKILL.md` contains the `## Security & Secrets` section and the
  "Never commit secrets" rule.

Pre-commit mode (`--staged`): inspects only what is staged — staged filenames against the
secret-file patterns and staged content for secret values.

## Usage

```bash
# Full audit of the current repo
python3 tests/check_security_guidelines.py

# Audit another repo (e.g. the main integration repo)
python3 tests/check_security_guidelines.py --repo /Users/mackitchin/Repos/sfmc-crm-integration

# Fast audit without the history scan
python3 tests/check_security_guidelines.py --no-history

# Pre-commit mode: only what is staged
python3 tests/check_security_guidelines.py --staged
```

Exit codes: `0` = all passed, `1` = one or more failed, `2` = usage/setup error.

## Wire it into a pre-commit hook

```bash
cat > .git/hooks/pre-commit <<'SH'
#!/bin/sh
python3 tests/check_security_guidelines.py --staged || {
  echo "Commit blocked: security guideline check failed." >&2
  exit 1
}
SH
chmod +x .git/hooks/pre-commit
```

## Wire it into CI (GitHub Actions)

```yaml
- name: Security guideline check
  run: python3 tests/check_security_guidelines.py
```

## Tuning

The expectations live at the top of `check_security_guidelines.py`:
`REQUIRED_GITIGNORE_PATTERNS`, `SECRET_FILE_GLOBS`, `SECRET_VALUE_PATTERNS`, and
`PLACEHOLDER_MARKERS`. Keep them in sync with `SKILL.md` and `.gitignore` when the
standards change. If the scanner ever flags a legitimate placeholder, add a distinguishing
marker to `PLACEHOLDER_MARKERS` rather than weakening a detector.
