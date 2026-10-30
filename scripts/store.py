"""The PuffPAI Store's checks and index builder.

    python scripts/store.py check [ids...]   check index rows (all, or the ids given); exit 1 on any problem
    python scripts/store.py build            check every row, then write index.json

Each row in ``index/<id>.json`` names a repo, a folder in it and one commit. This script fetches exactly that
commit, reads the package's own ``puffpai.json``, checks the row against it, then runs ``puffpai check`` on the
folder (the Core's "Works on PuffPAI" levels, which include the manifest, look-value and picture rules and
Drawbridge). Community rows need Level 1; Verified rows need Level 3.

Standard library only. Needs ``git`` and, unless ``--no-puffpai-check``, the ``puffpai`` command on PATH.
For a repo not on GitHub yet, ``--local URL=PATH`` fetches from a folder on this computer instead.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX_DIR = ROOT / "index"
YANKED = ROOT / "yanked.json"
OUT = ROOT / "index.json"

ID = re.compile(r"^[a-z][a-z0-9-]{1,39}$")
SHA = re.compile(r"^[0-9a-f]{40}$")
REPO = re.compile(r"^https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
KINDS = {"app", "tool", "skill", "page", "ui", "avatar", "look", "agent", "knowledge", "bundle", "provider"}
TIERS = {"community", "verified"}
ROW_KEYS = {"id", "kind", "repo", "path", "commit", "tier", "verified_by", "verified_commit", "notes"}
#: Open source licenses the store takes (SPDX ids). Ask in an issue to add one.
LICENSES = {"Apache-2.0", "MIT", "BSD-2-Clause", "BSD-3-Clause", "ISC", "MPL-2.0", "GPL-2.0-only",
            "GPL-2.0-or-later", "GPL-3.0-only", "GPL-3.0-or-later", "AGPL-3.0-only", "AGPL-3.0-or-later",
            "LGPL-2.1-only", "LGPL-2.1-or-later", "LGPL-3.0-only", "LGPL-3.0-or-later", "Unlicense",
            "CC0-1.0", "CC-BY-4.0", "CC-BY-SA-4.0", "0BSD", "Zlib"}
#: Levels a tier needs from ``puffpai check``.
NEEDS = {"community": 1, "verified": 3}
RESULT = re.compile(r"^Result: .*?(?:passes|passes up to) Level (\d)")
OPEN_ITEM = re.compile(r"^\s*(?:Level \d \S+\s+)?----\s+(\d+): not checked")


def git(*args: str, cwd: Path | None = None) -> str:
    done = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=300)
    if done.returncode != 0:
        raise RuntimeError(f"git {' '.join(args[:2])} failed: {done.stderr.strip()[:300]}")
    return done.stdout


def fetch(repo: str, commit: str, local: dict[str, str], cache: dict, work: Path) -> Path:
    """A checkout of exactly ``commit``; one per repo and commit."""
    key = (repo, commit)
    if key not in cache:
        dst = work / f"r{len(cache)}"
        dst.mkdir()
        git("init", "-q", cwd=dst)
        source = local.get(repo, repo)
        try:
            git("fetch", "-q", "--depth", "1", source, commit, cwd=dst)
        except RuntimeError:
            git("fetch", "-q", source, cwd=dst)                       # a server that won't serve one commit
        git("-c", "advice.detachedHead=false", "checkout", "-q", commit, cwd=dst)
        cache[key] = dst
    return cache[key]


def row_problems(name: str, row: object) -> list[str]:
    if not isinstance(row, dict):
        return ["the file is not a JSON object"]
    out = [f"unknown field {k!r}" for k in row if k not in ROW_KEYS]
    rid = row.get("id")
    if not isinstance(rid, str) or not ID.match(rid):
        out.append("id must be 2 to 40 characters: lower-case letters, digits or '-', starting with a letter")
    elif name != f"{rid}.json":
        out.append(f"the file must be named {rid}.json")
    if row.get("kind") not in KINDS:
        out.append(f"kind must be one of {', '.join(sorted(KINDS))}")
    if not isinstance(row.get("repo"), str) or not REPO.match(row["repo"]):
        out.append("repo must be https://github.com/<owner>/<repo>")
    path = row.get("path", "")
    if not isinstance(path, str) or path.startswith(("/", "\\")) or ".." in Path(path).parts or "\\" in path:
        out.append("path must be a folder inside the repo, like 'my-app' (or empty for the repo root)")
    if not isinstance(row.get("commit"), str) or not SHA.match(row["commit"]):
        out.append("commit must be a full 40-character commit id")
    if row.get("tier") not in TIERS:
        out.append("tier must be community or verified")
    if row.get("tier") == "verified" and (row.get("verified_commit") != row.get("commit") or not row.get("verified_by")):
        out.append("a verified row needs verified_by and verified_commit equal to commit (a new commit needs a new review)")
    return out


def puffpai_check(folder: Path) -> tuple[int, list[str], list[str]]:
    """``puffpai check`` on ``folder``: (level passed, items not checked, the report's lines)."""
    exe = shutil.which("puffpai")
    if exe is None:
        raise RuntimeError("the puffpai command is not on PATH (install puffpai-core, or pass --no-puffpai-check)")
    done = subprocess.run([exe, "check", str(folder)], capture_output=True, text=True, timeout=900)
    lines = done.stdout.splitlines()
    level = 0
    for line in lines:
        m = RESULT.match(line)
        if m:
            level = int(m.group(1))
    unchecked = [m.group(1) for line in lines if (m := OPEN_ITEM.match(line))]
    return level, unchecked, lines


def check_row(file: Path, local: dict[str, str], cache: dict, work: Path, run_check: bool) -> tuple[dict | None, list[str]]:
    try:
        row = json.loads(file.read_text(encoding="utf-8"))
    except ValueError as e:
        return None, [f"not valid JSON: {e}"]
    problems = row_problems(file.name, row)
    if problems:
        return None, problems
    try:
        folder = fetch(row["repo"], row["commit"], local, cache, work) / row.get("path", "")
    except RuntimeError as e:
        return None, [f"could not fetch {row['repo']} at {row['commit'][:12]}: {e}"]
    try:
        m = json.loads((folder / "puffpai.json").read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None, [f"no readable puffpai.json in {row.get('path') or 'the repo root'} at that commit"]
    if m.get("id") != row["id"]:
        problems.append(f"puffpai.json says id {m.get('id')!r}, the row says {row['id']!r}")
    if m.get("kind") != row["kind"]:
        problems.append(f"puffpai.json says kind {m.get('kind')!r}, the row says {row['kind']!r}")
    if m.get("license") not in LICENSES:
        problems.append(f"license {m.get('license')!r} is not on the store's open source list")
    for need in ("name", "description", "version", "author"):
        if not isinstance(m.get(need), str) or not m[need].strip():
            problems.append(f"puffpai.json needs {need}")
    out = {"id": row["id"], "kind": row["kind"], "name": m.get("name"), "description": m.get("description"),
           "version": m.get("version"), "author": m.get("author"), "license": m.get("license"),
           "repo": row["repo"], "path": row.get("path", ""), "commit": row["commit"], "tier": row["tier"]}
    icon = m.get("icon")
    if isinstance(icon, str) and (folder / icon).is_file():
        base = "/".join(p for p in (row.get("path", ""), icon) if p)
        out["icon"] = f"{row['repo'].replace('github.com', 'raw.githubusercontent.com')}/{row['commit']}/{base}"
    if row["tier"] == "verified":
        out["verified_by"] = row["verified_by"]
    if run_check:
        try:
            level, unchecked, lines = puffpai_check(folder)
        except (RuntimeError, subprocess.TimeoutExpired) as e:
            return None, problems + [str(e)]
        out["levels"] = list(range(1, level + 1))
        if unchecked:
            out["not_checked"] = unchecked
        if level < NEEDS[row["tier"]]:
            problems.append(f"puffpai check passes Level {level}; a {row['tier']} row needs Level {NEEDS[row['tier']]}")
            problems += [f"    {line}" for line in lines if "FAIL" in line]
    return out, problems


def yanked_problems() -> list[str]:
    try:
        data = json.loads(YANKED.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return [f"yanked.json: {e}"]
    if not isinstance(data, list):
        return ["yanked.json must be a list"]
    out = []
    for i, y in enumerate(data):
        if not (isinstance(y, dict) and isinstance(y.get("id"), str) and isinstance(y.get("why"), str)
                and isinstance(y.get("commit"), str) and SHA.match(y["commit"])):
            out.append(f"yanked.json entry {i}: needs id, a 40-character commit and why")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("action", choices=("check", "build"))
    ap.add_argument("ids", nargs="*", help="check only these ids (check only)")
    ap.add_argument("--local", action="append", default=[], metavar="URL=PATH",
                    help="fetch this repo URL from a folder on this computer (before it is on GitHub)")
    ap.add_argument("--no-puffpai-check", action="store_true", help="skip puffpai check (levels left out)")
    args = ap.parse_args(argv)
    local = dict(pair.split("=", 1) for pair in args.local)
    files = sorted(INDEX_DIR.glob("*.json"))
    if args.action == "check" and args.ids:
        files = [f for f in files if f.stem in args.ids] or [INDEX_DIR / f"{i}.json" for i in args.ids]
    bad, rows = yanked_problems(), []
    with tempfile.TemporaryDirectory(prefix="puffpai-store-") as tmp:
        cache: dict = {}
        for file in files:
            if not file.is_file():
                bad.append(f"{file.name}: no such row")
                continue
            row, problems = check_row(file, local, cache, Path(tmp), not args.no_puffpai_check)
            status = "FAIL" if problems else "PASS"
            levels = "" if not row or "levels" not in row else f"  Level {len(row['levels'])}"
            print(f"{status}  {file.stem}{levels}")
            for p in problems:
                print(f"      {p}")
            bad += [f"{file.stem}: {p}" for p in problems]
            if row:
                rows.append(row)
    if args.action == "build" and not bad:
        OUT.write_text(json.dumps({"schema": "puffpai-store-index/1", "name": "PuffPAI Store", "packages": rows,
                                   "yanked": json.loads(YANKED.read_text(encoding="utf-8"))},
                                  indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"wrote {OUT.name}: {len(rows)} packages")
    if bad:
        print(f"\n{len(bad)} problem(s).")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
