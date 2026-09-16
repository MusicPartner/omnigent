from __future__ import annotations

from pathlib import Path
import re

resolver = Path('.github/scripts/windows_parity_resolve.py')
source = resolver.read_text()
source, n = re.subn(
    r"# npm executable name differs under native Windows CreateProcess\..*?(?=# Add parser regressions)",
    "",
    source,
    count=1,
    flags=re.S,
)
if n != 1:
    raise SystemExit(f'expected one obsolete npm resolver block, got {n}')

# Execute the guarded production reconciliation without mutating the stored v1
# helper. Every production edit still fails closed on an unexpected v0.14 shape.
exec(compile(source, str(resolver), 'exec'), {'__name__': '__main__'})

# v0.14 moved the frontend fixture from npm to pnpm. Preserve the Windows
# executable-name intent while retaining v0.14's frozen root-workspace install.
p = Path('tests/e2e_ui/conftest.py')
text = p.read_text()
old = '''        env = {**os.environ, "COREPACK_ENABLE_DOWNLOAD_PROMPT": "0"}
        subprocess.run(
            ["pnpm", "install", "--frozen-lockfile", "--filter", "web"],
            cwd=_REPO_ROOT,
            check=True,
            stdin=subprocess.DEVNULL,
            env=env,
        )
        subprocess.run(
            ["pnpm", "--filter", "web", "run", "build"],
            cwd=_REPO_ROOT,
            check=True,
            stdin=subprocess.DEVNULL,
            env=env,
        )
'''
new = '''        env = {**os.environ, "COREPACK_ENABLE_DOWNLOAD_PROMPT": "0"}
        pnpm = "pnpm.cmd" if sys.platform == "win32" else "pnpm"
        subprocess.run(
            [pnpm, "install", "--frozen-lockfile", "--filter", "web"],
            cwd=_REPO_ROOT,
            check=True,
            stdin=subprocess.DEVNULL,
            env=env,
        )
        subprocess.run(
            [pnpm, "--filter", "web", "run", "build"],
            cwd=_REPO_ROOT,
            check=True,
            stdin=subprocess.DEVNULL,
            env=env,
        )
'''
if old not in text:
    raise SystemExit('v0.14 pnpm build fixture changed unexpectedly')
p.write_text(text.replace(old, new, 1))
