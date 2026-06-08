#!/usr/bin/env python3
"""Validate that the security guidelines documented in SKILL.md are upheld.

This is a guardrail, not a guarantee: it mechanically verifies the parts of the
SKILL.md "Security & Secrets" standards that *can* be checked against the
repository state, so an agent (or CI, or a pre-commit hook) can catch the most
common ways a credential leaks into version control.

Checks (full audit, default):
  1. gitignore-coverage   .gitignore exists and lists the documented secret
                          patterns (.env, client_secret*, *.secret, *.token,
                          *.pem, *.key).
  2. gitignore-effective  git actually ignores representative secret files
                          (uses `git check-ignore`).
  3. no-secret-files      No secret-bearing files are tracked by git.
  4. no-secret-values     No real secret VALUES appear in tracked text content
                          (obvious placeholders like YOUR_SECRET are allowed).
  5. history-clean        No real secret values appear anywhere in git history
                          (skip with --no-history).
  6. docs-present         SKILL.md documents the Security & Secrets standards.

Pre-commit mode (--staged): only inspects what is staged for commit -- staged
filenames against the secret-file patterns and staged content for secret
values. Wire it into .git/hooks/pre-commit to enforce "verify before commit".

Usage:
  python3 check_security_guidelines.py [--repo PATH] [--staged] [--no-history]

Exit codes: 0 = all checks passed, 1 = one or more failed, 2 = usage/setup error.
No third-party dependencies; Python 3.8+.
"""
from __future__ import annotations

import argparse
import fnmatch
import os
import re
import subprocess
import sys

# --- Documented expectations (keep in sync with SKILL.md / .gitignore) --------

# Patterns the .gitignore must list (the secret types SKILL.md calls out).
REQUIRED_GITIGNORE_PATTERNS = [
    ".env",
    "client_secret*",
    "*.secret",
    "*.token",
    "*.pem",
    "*.key",
]

# Representative secret files that git must actually ignore.
MUST_BE_IGNORED = [".env", "client_secret.txt", "service.pem", "api.token", "id_rsa.key"]

# A tracked file matching any of these globs is treated as a leaked secret file.
SECRET_FILE_GLOBS = [
    ".env", ".env.*",
    "client_secret*", "*.secret", "secrets.*",
    "*.token", "*.pem", "*.key", "*.p12", "*.pfx", "*.keytab",
    "credentials", "credentials.json", "id_rsa", "id_rsa.*", ".netrc",
]
# ...but these "safe sample" names are explicitly allowed even if tracked.
SECRET_FILE_ALLOW = ["*.example", "*.sample", "*.template", "*.dist"]

# Secret VALUE detectors. Each entry is (name, compiled-regex). The capture
# group (when present) is the candidate secret value; group-less patterns use
# the whole match.
SECRET_VALUE_PATTERNS = [
    ("private-key-block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("github-token", re.compile(r"\b(?:gho|ghp|ghs|ghr|github_pat)_[A-Za-z0-9_]{20,}")),
    ("aws-access-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("slack-token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}")),
    ("bearer-token", re.compile(r"[Bb]earer\s+([A-Za-z0-9._~+/-]{20,}=*)")),
    (
        "assigned-credential",
        re.compile(
            r"(?i)\b(client_secret|api[_-]?key|access[_-]?token|refresh[_-]?token|"
            r"secret[_-]?key|password|passwd)\b\s*[:=]\s*['\"]?([^\s'\"#,)]{8,})"
        ),
    ),
]

# If a candidate value (lowercased) contains any of these, it's a placeholder,
# not a real secret -- don't flag it.
PLACEHOLDER_MARKERS = [
    "your", "example", "sample", "placeholder", "change", "redact", "dummy",
    "replace", "xxxx", "<", "{{", "***", "...", "env", "getenv", "os.environ",
    "process.env", "$", "todo", "fixme", "secret",  # e.g. YOUR_SECRET, my_secret
    "test", "fake", "none", "null",
]


# --- Result plumbing ----------------------------------------------------------

class Result:
    def __init__(self, name: str):
        self.name = name
        self.status = "PASS"   # PASS | FAIL | SKIP | ERROR
        self.findings: list[str] = []

    def fail(self, msg: str):
        self.status = "FAIL"
        self.findings.append(msg)

    def skip(self, msg: str):
        if self.status == "PASS":
            self.status = "SKIP"
        self.findings.append(msg)

    def error(self, msg: str):
        self.status = "ERROR"
        self.findings.append(msg)


def git(repo: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", repo, *args],
        capture_output=True, text=True,
    )


def git_bytes(repo: str, *args: str) -> subprocess.CompletedProcess:
    """Like git() but returns raw bytes (for blob content that may be binary)."""
    return subprocess.run(["git", "-C", repo, *args], capture_output=True)


def is_placeholder(value: str) -> bool:
    v = value.strip().lower()
    return any(marker in v for marker in PLACEHOLDER_MARKERS)


def mask(value: str) -> str:
    value = value.strip()
    if len(value) <= 6:
        return value[0] + "***" if value else "***"
    return f"{value[:4]}…{value[-2:]} (len {len(value)})"


def allowed_sample(path: str) -> bool:
    base = os.path.basename(path)
    return any(fnmatch.fnmatch(base, g) for g in SECRET_FILE_ALLOW)


def looks_secret_file(path: str) -> bool:
    base = os.path.basename(path)
    if allowed_sample(path):
        return False
    return any(fnmatch.fnmatch(base, g) for g in SECRET_FILE_GLOBS)


def scan_text_for_secrets(text: str, path: str) -> list[str]:
    """Return human-readable findings for real secret values in `text`."""
    findings: list[str] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for name, rx in SECRET_VALUE_PATTERNS:
            for m in rx.finditer(line):
                value = m.group(m.lastindex) if m.lastindex else m.group(0)
                if is_placeholder(value):
                    continue
                findings.append(f"{path}:{lineno}: {name}: {mask(value)}")
    return findings


# --- Individual checks --------------------------------------------------------

def check_gitignore_coverage(repo: str) -> Result:
    r = Result("gitignore-coverage")
    path = os.path.join(repo, ".gitignore")
    if not os.path.isfile(path):
        r.fail("no .gitignore at repo root")
        return r
    with open(path, encoding="utf-8", errors="replace") as fh:
        lines = {ln.strip() for ln in fh}
    for pat in REQUIRED_GITIGNORE_PATTERNS:
        if pat not in lines:
            r.fail(f"missing required pattern: {pat}")
    return r


def check_gitignore_effective(repo: str) -> Result:
    r = Result("gitignore-effective")
    for f in MUST_BE_IGNORED:
        cp = git(repo, "check-ignore", "-q", "--no-index", f)
        # exit 0 => ignored; 1 => not ignored; 128 => error
        if cp.returncode == 1:
            r.fail(f"git would NOT ignore {f}")
        elif cp.returncode not in (0, 1):
            r.error(f"git check-ignore failed for {f}: {cp.stderr.strip()}")
    return r


def tracked_files(repo: str) -> list[str]:
    cp = git(repo, "ls-files")
    if cp.returncode != 0:
        raise RuntimeError(cp.stderr.strip() or "git ls-files failed")
    return [p for p in cp.stdout.splitlines() if p]


def check_no_secret_files(repo: str) -> Result:
    r = Result("no-secret-files")
    for path in tracked_files(repo):
        if looks_secret_file(path):
            r.fail(f"secret-bearing file is tracked: {path}")
    return r


def check_no_secret_values(repo: str, self_rel: str | None) -> Result:
    r = Result("no-secret-values")
    for path in tracked_files(repo):
        if self_rel and os.path.normpath(path) == self_rel:
            continue  # don't scan the scanner's own pattern literals
        full = os.path.join(repo, path)
        try:
            with open(full, encoding="utf-8") as fh:
                text = fh.read()
        except (UnicodeDecodeError, FileNotFoundError, IsADirectoryError):
            continue  # binary or unreadable -> skip
        for finding in scan_text_for_secrets(text, path):
            r.fail(finding)
    return r


def check_history_clean(repo: str, self_rel: str | None) -> Result:
    """Scan every unique text blob ever committed for real secret values.

    Reads blobs in Python and reuses scan_text_for_secrets so the detection
    logic is identical to the working-tree check (git grep can't run the same
    regexes -- it uses POSIX ERE without \\b, (?:...), lookarounds, etc.).
    """
    r = Result("history-clean")
    revs = git(repo, "rev-list", "--objects", "--all")
    if revs.returncode != 0:
        r.error(revs.stderr.strip() or "git rev-list failed")
        return r
    if not revs.stdout.strip():
        r.skip("no commits yet")
        return r
    seen: set[str] = set()
    for line in revs.stdout.splitlines():
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            continue  # commit oid (no path) or blank line
        oid, path = parts[0], parts[1]
        if oid in seen:
            continue
        seen.add(oid)
        if self_rel and os.path.normpath(path) == self_rel:
            continue
        t = git(repo, "cat-file", "-t", oid)
        if t.returncode != 0 or t.stdout.strip() != "blob":
            continue  # only scan blobs, not trees
        raw = git_bytes(repo, "cat-file", "-p", oid).stdout
        if b"\x00" in raw:
            continue  # binary blob
        text = raw.decode("utf-8", "replace")
        for finding in scan_text_for_secrets(text, f"{path}@{oid[:9]}"):
            r.fail(finding)
    return r


def find_skill_md(repo: str) -> str | None:
    root = os.path.join(repo, "SKILL.md")
    if os.path.isfile(root):
        return "SKILL.md"
    for path in tracked_files(repo):
        if os.path.basename(path) == "SKILL.md":
            return path
    return None


def check_docs_present(repo: str) -> Result:
    r = Result("docs-present")
    rel = find_skill_md(repo)
    if not rel:
        r.skip("no SKILL.md in this repo")
        return r
    with open(os.path.join(repo, rel), encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    if "## Security & Secrets" not in text:
        r.fail(f"{rel}: missing '## Security & Secrets' section")
    if not re.search(r"(?i)never commit secrets", text):
        r.fail(f"{rel}: missing the 'Never commit secrets' rule")
    return r


# --- Staged (pre-commit) mode -------------------------------------------------

def check_staged(repo: str, self_rel: str | None) -> list[Result]:
    files_r = Result("staged-no-secret-files")
    values_r = Result("staged-no-secret-values")
    cp = git(repo, "diff", "--cached", "--name-only", "--diff-filter=ACM")
    if cp.returncode != 0:
        files_r.error(cp.stderr.strip() or "git diff --cached failed")
        return [files_r]
    staged = [p for p in cp.stdout.splitlines() if p]
    if not staged:
        files_r.skip("nothing staged")
        values_r.skip("nothing staged")
        return [files_r, values_r]
    for path in staged:
        if looks_secret_file(path):
            files_r.fail(f"secret-bearing file staged: {path}")
        if self_rel and os.path.normpath(path) == self_rel:
            continue
        blob = git(repo, "show", f":{path}")
        if blob.returncode != 0:
            continue
        for finding in scan_text_for_secrets(blob.stdout, path):
            values_r.fail("STAGED " + finding)
    return [files_r, values_r]


# --- Driver -------------------------------------------------------------------

def repo_root(start: str) -> str:
    cp = subprocess.run(
        ["git", "-C", start, "rev-parse", "--show-toplevel"],
        capture_output=True, text=True,
    )
    if cp.returncode != 0:
        raise RuntimeError(f"not inside a git repo: {start}")
    return cp.stdout.strip()


def self_relpath(repo: str) -> str | None:
    try:
        return os.path.normpath(os.path.relpath(os.path.abspath(__file__), repo))
    except ValueError:
        return None


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=".",
                    help="path inside the repo to validate (default: cwd)")
    ap.add_argument("--staged", action="store_true",
                    help="pre-commit mode: only inspect staged changes")
    ap.add_argument("--no-history", action="store_true",
                    help="skip the full git-history scan")
    args = ap.parse_args(argv)

    try:
        repo = repo_root(args.repo)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    self_rel = self_relpath(repo)

    print(f"Security guideline check  repo={repo}")
    print(f"mode={'staged' if args.staged else 'full'}\n")

    try:
        if args.staged:
            results = check_staged(repo, self_rel)
        else:
            results = [
                check_gitignore_coverage(repo),
                check_gitignore_effective(repo),
                check_no_secret_files(repo),
                check_no_secret_values(repo, self_rel),
                check_docs_present(repo),
            ]
            if not args.no_history:
                results.append(check_history_clean(repo, self_rel))
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    icon = {"PASS": "PASS ", "FAIL": "FAIL ", "SKIP": "SKIP ", "ERROR": "ERROR"}
    failed = errored = 0
    for res in results:
        print(f"[{icon[res.status]}] {res.name}")
        for f in res.findings:
            print(f"         - {f}")
        if res.status == "FAIL":
            failed += 1
        elif res.status == "ERROR":
            errored += 1

    print()
    if failed or errored:
        print(f"RESULT: FAIL ({failed} failed, {errored} errored)")
        return 1
    print("RESULT: PASS (all security guideline checks satisfied)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
