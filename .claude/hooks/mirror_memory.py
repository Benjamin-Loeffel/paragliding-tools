#!/usr/bin/env python3
"""PostToolUse-Hook: spiegelt jede Schreiboperation auf eine Auto-Memory-Datei
(``~/.claude/projects/<projekt>/memory/*.md``) automatisch ins Repo nach
``.claude/agent-memory/`` — damit das projektübergreifende Memory wie die ADRs
versioniert und teilbar ist (Idee des Autors, 2026-06-30; ADR-0032).

Registriert in ``.claude/settings.json`` (PostToolUse, Matcher ``Write|Edit``).
Liest die Tool-Payload von stdin (``tool_input.file_path`` — gleich für Write & Edit).
Exit 0 = still (kein Memory-File ⇒ no-op). Fehler ⇒ stderr + Exit 1 (nicht blockierend,
PostToolUse: das Tool lief bereits).
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path


def main() -> int:
    raw = sys.stdin.read()
    if not raw.strip():
        return 0
    try:
        ev = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"mirror_memory: stdin kein JSON: {exc}", file=sys.stderr)
        return 1

    fp = (ev.get("tool_input") or {}).get("file_path")
    if not fp:
        return 0
    src = Path(fp)

    # Nur die auto-geladene Memory-Ablage spiegeln: .../.claude/.../memory/<name>.md
    # (NICHT die Repo-Kopie .claude/agent-memory/ — anderer Ordnername ⇒ keine Rekursion)
    parts = [p.lower() for p in src.parts]
    is_memory = (src.suffix.lower() == ".md"
                 and src.parent.name.lower() == "memory"
                 and ".claude" in parts)
    if not is_memory or not src.exists():
        return 0

    root = os.environ.get("CLAUDE_PROJECT_DIR") or ev.get("cwd") or os.getcwd()
    dest_dir = Path(root) / ".claude" / "agent-memory"
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest_dir / src.name)
    except OSError as exc:
        print(f"mirror_memory: Kopieren fehlgeschlagen ({src} -> {dest_dir}): {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
