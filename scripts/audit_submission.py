"""Audit actual Git index blobs without printing credential values (stdlib only)."""
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLOCKED_DIRS = {
    'node_modules', '.venv', '__pycache__', '.pytest_cache', '.cache',
    '.submission-work', '.vercel', 'dist', 'build', 'coverage', 'artifacts',
    'playwright-report', 'logs', '.test-tmp',
}
PATTERNS = {
    'provider_key': re.compile(rb'\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{24,}'),
    'github_token': re.compile(rb'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})'),
    'aws_access_key': re.compile(rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
    'google_api_key': re.compile(rb'\bAIza[0-9A-Za-z_-]{35}\b'),
    'slack_token': re.compile(rb'\bxox[baprs]-[A-Za-z0-9-]{20,}'),
    'private_key': re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'windows_absolute_path': re.compile(rb'(?<![A-Za-z])[A-Za-z]:[\\/](?![\\/])'),
    'unix_personal_path': re.compile(rb'/(?:Users|home)/[A-Za-z0-9_.-]+/'),
}
REQUIRED = {
    'README.md', 'SUBMISSION_ACCEPTANCE.md', '.gitignore',
    'task1-chatroom/README.md', 'task1-chatroom/ACCEPTANCE.md',
    'task1-chatroom/REAL_LLM_VALIDATION.md', 'task1-chatroom/backend/.env.example',
    'task1-chatroom/backend/requirements.txt', 'task1-chatroom/backend/requirements-lock.txt',
    'task1-chatroom/frontend/package.json', 'task1-chatroom/frontend/package-lock.json',
    'task1-chatroom/frontend/tests/chatroom.spec.ts',
    'task2-landing/README.md', 'task2-landing/DELIVERY.md',
    'task2-landing/.env.example', 'task2-landing/package.json', 'task2-landing/package-lock.json',
    'task2-landing/tests/landing.spec.ts', 'task2-landing/tests/workspace-url.spec.ts',
}


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])


def audit():
    entries = git('ls-files', '--stage', '-z').split(b'\0')
    findings, paths, total_bytes, largest_bytes = [], set(), 0, 0
    for entry in filter(None, entries):
        metadata, raw_path = entry.split(b'\t', 1)
        mode, oid, stage = metadata.decode().split()
        name = raw_path.decode('utf-8')
        paths.add(name)
        path = Path(name)
        parts = path.parts
        if mode not in {'100644', '100755'} or stage != '0':
            findings.append({'path': name, 'kind': 'symlink_submodule_or_unmerged'})
            continue
        forbidden = (any(p in BLOCKED_DIRS or p.startswith('test-results') for p in parts)
                     or (path.name.startswith('.env') and path.name != '.env.example')
                     or re.search(r'\.(?:db|sqlite3?)(?:-|$)', path.name)
                     or path.suffix.lower() in {'.zip', '.log', '.pyc', '.tsbuildinfo', '.pem', '.key', '.pfx'})
        if forbidden:
            findings.append({'path': name, 'kind': 'private_or_generated_file'})
        content = git('cat-file', 'blob', oid)
        total_bytes += len(content)
        largest_bytes = max(largest_bytes, len(content))
        if len(content) > 5 * 1024 * 1024:
            findings.append({'path': name, 'kind': 'oversized_file'})
        if b'\0' in content or content.startswith(b'SQLite format 3'):
            findings.append({'path': name, 'kind': 'unexpected_binary_or_database'})
        for kind, pattern in PATTERNS.items():
            if pattern.search(content):
                findings.append({'path': name, 'kind': kind})
    for name in sorted(REQUIRED - paths):
        findings.append({'path': name, 'kind': 'missing_required_file'})
    if not any(p.startswith('task1-chatroom/backend/tests/test_') for p in paths):
        findings.append({'path': 'task1-chatroom/backend/tests', 'kind': 'missing_backend_tests'})
    result = {
        'scope': 'actual_git_index_blobs', 'files_scanned': len(paths),
        'total_bytes': total_bytes, 'largest_file_bytes': largest_bytes,
        'findings': findings, 'result': 'PASS' if paths and not findings else 'FAIL',
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['result'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(audit())
