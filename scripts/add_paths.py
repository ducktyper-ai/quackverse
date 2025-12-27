#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import subprocess
from pathlib import Path
from typing import Iterable, Optional, Tuple

SKIP_DIR_PARTS = {
    ".git", ".venv", "__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache",
    "build", "dist", ".egg-info", "node_modules",
}

BEGIN = "# === QV-LLM:BEGIN ==="
END = "# === QV-LLM:END ==="

ENCODING_RE = re.compile(r"^#.*coding[:=]\s*[-\w.]+")
SHEBANG_RE = re.compile(r"^#!")

def iter_py_files(root: Path) -> Iterable[Path]:
    for dirpath, dirs, files in os.walk(root):
        dpath = Path(dirpath)
        # prune
        dirs[:] = [d for d in dirs if d not in SKIP_DIR_PARTS and d != "_transient-files"]
        for name in files:
            if name.endswith(".py"):
                yield dpath / name

def get_git_meta(repo_root: Path) -> dict:
    def run(cmd: list[str]) -> str:
        try:
            out = subprocess.check_output(cmd, cwd=repo_root, stderr=subprocess.DEVNULL)
            return out.decode().strip()
        except Exception:
            return ""

    return {
        "git_branch": run(["git", "rev-parse", "--abbrev-ref", "HEAD"]),
        "git_commit": run(["git", "rev-parse", "--short", "HEAD"]),
    }

def compute_module(relpath: str) -> Optional[str]:
    # heuristic: find ".../src/<pkg>/.../file.py"
    parts = relpath.split("/")
    if "src" not in parts:
        return None
    i = parts.index("src")
    tail = parts[i+1:]
    if not tail:
        return None
    if not tail[-1].endswith(".py"):
        return None
    tail[-1] = tail[-1][:-3]  # strip .py
    return ".".join(tail)

def infer_role(relpath: str) -> str:
    p = relpath.lower()
    for key in ["models", "protocols", "service", "operations", "plugin", "utils", "api", "cli", "adapters", "tests"]:
        if f"/{key}/" in p or p.endswith(f"/{key}.py"):
            return key
    return "module"

def build_block(relpath: str, module: Optional[str], git_meta: dict) -> list[str]:
    lines = [
        BEGIN,
        f"# path: {relpath}",
    ]
    if module:
        lines.append(f"# module: {module}")
    lines.append(f"# role: {infer_role(relpath)}")
    if git_meta.get("git_branch"):
        lines.append(f"# git_branch: {git_meta['git_branch']}")
    if git_meta.get("git_commit"):
        lines.append(f"# git_commit: {git_meta['git_commit']}")
    lines.append(END)
    return lines

def insert_or_replace_header(text: str, header_lines: list[str]) -> str:
    lines = text.splitlines()

    # detect insertion point: after shebang + encoding cookie (if present)
    idx = 0
    if idx < len(lines) and SHEBANG_RE.match(lines[idx]):
        idx += 1
    if idx < len(lines) and ENCODING_RE.match(lines[idx]):
        idx += 1

    # if existing block exists anywhere near the top, replace it
    # (we search first 50 lines to avoid accidental matches deep in the file)
    search_zone = "\n".join(lines[:50])
    if BEGIN in search_zone and END in search_zone:
        # replace the first occurrence block
        out = []
        i = 0
        replaced = False
        while i < len(lines):
            if not replaced and lines[i].strip() == BEGIN:
                # skip until END
                out.extend(lines[:i])  # keep everything before BEGIN
                out.extend(header_lines)
                # advance to line after END
                j = i + 1
                while j < len(lines) and lines[j].strip() != END:
                    j += 1
                if j < len(lines):  # include END line skip
                    j += 1
                out.extend(lines[j:])
                replaced = True
                break
            i += 1
        return "\n".join(out) + ("\n" if text.endswith("\n") else "")
    else:
        # insert at idx
        new_lines = lines[:idx] + header_lines + [""] + lines[idx:]
        return "\n".join(new_lines) + ("\n" if text.endswith("\n") else "")

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scope", default=".", help="Directory to process")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    scope = Path(args.scope).resolve()
    repo_root = Path(".").resolve()
    git_meta = get_git_meta(repo_root)

    changed = 0
    total = 0
    for f in sorted(iter_py_files(scope)):
        rel = f.relative_to(repo_root).as_posix()
        module = compute_module(rel)
        header = build_block(rel, module, git_meta)

        original = f.read_text(encoding="utf-8", errors="replace")
        updated = insert_or_replace_header(original, header)

        total += 1
        if updated != original:
            changed += 1
            if args.dry_run:
                print(f"[DRY] would update: {rel}")
            else:
                f.write_text(updated, encoding="utf-8")
                print(f"updated: {rel}")

    print(f"done: {changed}/{total} files updated")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
