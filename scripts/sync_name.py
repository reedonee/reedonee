"""Sync the display name from the GitHub profile into the animated SVGs.

Reads the owner's profile name from the GitHub API and rewrites every
<text id="profile-name"> element in assets/header.svg and assets/terminal.svg,
plus the header alt text in README.md. Prints whether anything changed.
"""
import json
import os
import re
import urllib.request
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOGIN = os.environ.get("PROFILE_LOGIN", "reedonee")
TOKEN = os.environ.get("GITHUB_TOKEN", "")


def fetch_name() -> str:
    req = urllib.request.Request(
        f"https://api.github.com/users/{LOGIN}",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "profile-name-sync"},
    )
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.load(r)
    return (data.get("name") or LOGIN).strip()


def replace_text(path: Path, new_inner: str) -> bool:
    src = path.read_text(encoding="utf-8")
    out, n = re.subn(
        r'(<text id="profile-name"[^>]*>)(.*?)(</text>)',
        lambda m: m.group(1) + new_inner + m.group(3),
        src,
        flags=re.S,
    )
    if n == 0:
        raise SystemExit(f"no profile-name element in {path}")
    if out != src:
        path.write_text(out, encoding="utf-8")
        return True
    return False


def main() -> None:
    name = fetch_name()
    safe = escape(name)
    changed = False
    changed |= replace_text(ROOT / "assets/header.svg", f"{escape(name.upper())} · FULL-STACK BUILDER")
    changed |= replace_text(ROOT / "assets/terminal.svg", f"{safe}  //  full-stack builder  //  @{LOGIN}")

    readme = ROOT / "README.md"
    src = readme.read_text(encoding="utf-8")
    out = re.sub(r'alt="RED — [^"]*, full-stack builder"', f'alt="RED — {safe}, full-stack builder"', src)
    out = re.sub(r'alt="whoami: [^,"]*, full-stack builder\.', f'alt="whoami: {safe}, full-stack builder.', out)
    if out != src:
        readme.write_text(out, encoding="utf-8")
        changed = True

    print(f"name={name!r} changed={changed}")


if __name__ == "__main__":
    main()
