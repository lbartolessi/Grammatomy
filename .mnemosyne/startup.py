#!/usr/bin/env python3
"""Auto-startup helper: read and summarize the two latest chronicles.

Usage: python .mnemosyne/startup.py
"""
import re
from pathlib import Path

SUMMARY = "SUMMARY:"


def chapter_number(name: str) -> int:
    m = re.search(r"chapter_(\d+)", name)
    return int(m.group(1)) if m else -1


def should_stop_capture(line: str) -> bool:
    """Check if we should stop capturing summary lines."""
    return not line or line.startswith("NEXT IMMEDIATE STEP") or line.startswith("##")


def extract_summary(text: str) -> str:
    lines = text.splitlines()
    summary_lines = []
    capture = False
    for ln in lines:
        s = ln.strip()
        if capture:
            if should_stop_capture(s):
                break
            summary_lines.append(s)
        elif s == SUMMARY or s.startswith(SUMMARY):
            rest = s[len(SUMMARY) :].strip()
            if rest:
                summary_lines.append(rest)
            capture = True
    return " ".join(summary_lines).strip()


def summarize_chapter(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    title = path.stem.replace("_", " ")
    m = re.search(r"#\s*CHRONICLE:\s*(.+)", text)
    if m:
        title = m.group(1).strip()
    summary = extract_summary(text)
    return f"{title}: {summary if summary else '(no SUMMARY found)'}"


def main():
    repo_root = Path(__file__).resolve().parents[1]
    chronicles_dir = repo_root / ".mnemosyne" / "chronicles"
    if not chronicles_dir.exists():
        print("No .mnemosyne/chronicles directory found.")
        return
    files = [p for p in chronicles_dir.iterdir() if p.is_file() and p.name.startswith("chapter_")]
    if not files:
        print("No chapter files found in .mnemosyne/chronicles.")
        return
    files.sort(key=lambda p: chapter_number(p.name))
    latest = files[-2:] if len(files) >= 2 else files
    print("Mnemosyne — resumiendo los últimos capítulos:\n")
    for f in latest:
        print(summarize_chapter(f))
        print()


if __name__ == "__main__":
    main()
