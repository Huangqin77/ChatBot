"""Read-only delivery scan. Report paths/counts, never secret contents."""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from app.config import Settings

SKIP = {'node_modules', '.venv', '.cache', '.git', '__pycache__', '.test-tmp', '.pytest_cache', 'test-results'}
PATTERNS = {
    'credential_pattern': re.compile(rb'sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{24,}'),
    'private_key': re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
}


def run():
    settings = Settings()
    findings, scanned, logs = [], 0, 0
    for path in ROOT.rglob('*'):
        relative = path.relative_to(ROOT)
        if any(part in SKIP for part in relative.parts) or not path.is_file():
            continue
        if path.suffix in {'.db', '.db-wal', '.db-shm', '.png', '.zip', '.pyc'}:
            continue
        if path.name.startswith('.env') and not path.name.endswith('.example') and relative.parts[0] == 'backend':
            continue  # This is the authorized local server secret file, not a deliverable.
        content = path.read_bytes()
        scanned += 1
        logs += int(path.suffix == '.log')
        for kind, pattern in PATTERNS.items():
            if pattern.search(content):
                findings.append({'path': relative.as_posix(), 'kind': kind})
        if settings.api_key and settings.api_key.encode() in content:
            findings.append({'path': relative.as_posix(), 'kind': 'configured_key'})
    git = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', '--show-toplevel'], capture_output=True)
    history = 'unavailable_no_git_repository'
    if git.returncode == 0:
        tracked = subprocess.run(['git', '-C', str(ROOT), 'ls-files', '-z'], capture_output=True, check=True).stdout.decode().split('\0')
        for path in tracked:
            name = Path(path).name
            if name.startswith('.env') and not name.endswith('.example'):
                findings.append({'path': path, 'kind': 'tracked_environment_file'})
        commits = subprocess.run(['git', '-C', str(ROOT), 'rev-list', '--all'], capture_output=True, check=True).stdout.decode().split()
        for commit in commits:
            # -l prints filenames only. Never print matched lines or credentials.
            match = subprocess.run(['git', '-C', str(ROOT), 'grep', '-I', '-l', '-E',
                                    r'sk-(proj-|svcacct-)?[A-Za-z0-9_-]{24,}', commit, '--', '.'], capture_output=True)
            for path in match.stdout.decode(errors='replace').splitlines():
                findings.append({'path': path, 'kind': 'git_history_credential_pattern'})
            historical = subprocess.run(['git', '-C', str(ROOT), 'ls-tree', '-r', '--name-only', commit], capture_output=True, check=True)
            for path in historical.stdout.decode(errors='replace').splitlines():
                if Path(path).name.startswith('.env') and not Path(path).name.endswith('.example'):
                    findings.append({'path': f'{commit}:{path}', 'kind': 'git_history_environment_file'})
        history = f'checked_{len(commits)}_commits'
    ignored = (ROOT / '.gitignore').read_text(encoding='utf-8').splitlines()
    if not {'.env', '.env.*', '!.env.example'} <= set(ignored):
        findings.append({'path': '.gitignore', 'kind': 'missing_environment_ignore_rules'})
    print(json.dumps({'files_scanned': scanned, 'log_files_scanned': logs,
                      'git_history': history, 'api_key_configured': bool(settings.api_key),
                      'findings': findings}, ensure_ascii=False, indent=2))
    return bool(findings)


if __name__ == '__main__':
    raise SystemExit(run())
