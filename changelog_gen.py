#!/usr/bin/env python3
"""changelog_gen - Changelog generator from git history.

Parse conventional commits, group by type, generate markdown changelogs. Zero deps.
"""

import argparse
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime


TYPES = {
    "feat": "✨ Features", "fix": "🐛 Bug Fixes", "docs": "📚 Documentation",
    "style": "💄 Style", "refactor": "♻️ Refactoring", "perf": "⚡ Performance",
    "test": "🧪 Tests", "build": "🏗️ Build", "ci": "🔄 CI",
    "chore": "🔧 Chores", "revert": "⏪ Reverts",
}

CC_RE = re.compile(r'^(?P<type>\w+)(?:\((?P<scope>[^)]+)\))?(?P<breaking>!)?\s*:\s*(?P<desc>.+)')


def run(cmd, cwd=None):
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    return r.stdout.strip() if r.returncode == 0 else ""


def get_tags(cwd):
    out = run(["git", "tag", "--sort=-creatordate", "--format=%(refname:short) %(creatordate:iso)"], cwd)
    tags = []
    for line in out.split("\n"):
        if not line.strip():
            continue
        parts = line.strip().split(" ", 1)
        tags.append({"name": parts[0], "date": parts[1].split()[0] if len(parts) > 1 else ""})
    return tags


def get_commits(cwd, since=None, until=None):
    cmd = ["git", "log", "--format=%H|%s|%an|%ad", "--date=short"]
    if since and until:
        cmd.append(f"{since}..{until}")
    elif since:
        cmd.append(f"{since}..HEAD")
    elif until:
        cmd.append(until)
    out = run(cmd, cwd)
    commits = []
    for line in out.split("\n"):
        if not line.strip():
            continue
        parts = line.split("|", 3)
        if len(parts) >= 4:
            commits.append({"hash": parts[0][:8], "msg": parts[1], "author": parts[2], "date": parts[3]})
    return commits


def classify(msg):
    m = CC_RE.match(msg)
    if m:
        return {
            "type": m.group("type"),
            "scope": m.group("scope") or "",
            "breaking": bool(m.group("breaking")),
            "desc": m.group("desc").strip(),
        }
    return {"type": "other", "scope": "", "breaking": False, "desc": msg}


def cmd_generate(args):
    cwd = args.repo or "."
    commits = get_commits(cwd, since=args.since, until=args.until)
    if not commits:
        print("No commits found")
        return

    grouped = defaultdict(list)
    breaking = []
    for c in commits:
        info = classify(c["msg"])
        c.update(info)
        grouped[info["type"]].append(c)
        if info["breaking"]:
            breaking.append(c)

    version = args.version or "Unreleased"
    date = datetime.now().strftime("%Y-%m-%d")
    print(f"## [{version}] - {date}\n")

    if breaking:
        print("### ⚠️ BREAKING CHANGES\n")
        for c in breaking:
            scope = f"**{c['scope']}**: " if c["scope"] else ""
            print(f"- {scope}{c['desc']} ({c['hash']})")
        print()

    for typ in list(TYPES.keys()) + ["other"]:
        if typ not in grouped:
            continue
        label = TYPES.get(typ, "📦 Other")
        print(f"### {label}\n")
        for c in grouped[typ]:
            scope = f"**{c['scope']}**: " if c["scope"] else ""
            print(f"- {scope}{c['desc']} ({c['hash']})")
        print()


def cmd_tags(args):
    cwd = args.repo or "."
    tags = get_tags(cwd)
    if not tags:
        print("No tags found")
        return
    for t in tags[:args.limit or 20]:
        print(f"  {t['name']:<20} {t['date']}")


def cmd_stats(args):
    cwd = args.repo or "."
    commits = get_commits(cwd, since=args.since)
    types = defaultdict(int)
    authors = defaultdict(int)
    scopes = defaultdict(int)
    breaking_count = 0

    for c in commits:
        info = classify(c["msg"])
        types[info["type"]] += 1
        authors[c["author"]] += 1
        if info["scope"]:
            scopes[info["scope"]] += 1
        if info["breaking"]:
            breaking_count += 1

    conventional = sum(v for k, v in types.items() if k in TYPES)
    total = len(commits)
    print(f"  Total commits: {total}")
    print(f"  Conventional: {conventional} ({conventional*100//total if total else 0}%)")
    print(f"  Breaking: {breaking_count}")
    print(f"\n  By type:")
    for typ, cnt in sorted(types.items(), key=lambda x: -x[1]):
        label = TYPES.get(typ, typ)
        print(f"    {cnt:>4}  {label}")
    print(f"\n  Top authors:")
    for author, cnt in sorted(authors.items(), key=lambda x: -x[1])[:5]:
        print(f"    {cnt:>4}  {author}")


def main():
    p = argparse.ArgumentParser(description="Changelog generator")
    sub = p.add_subparsers(dest="cmd")

    gp = sub.add_parser("generate", help="Generate changelog")
    gp.add_argument("--repo", default=".")
    gp.add_argument("--since", help="Start tag/commit")
    gp.add_argument("--until", help="End tag/commit")
    gp.add_argument("-v", "--version", help="Version label")

    tp = sub.add_parser("tags", help="List tags")
    tp.add_argument("--repo", default=".")
    tp.add_argument("-n", "--limit", type=int, default=20)

    sp = sub.add_parser("stats", help="Commit statistics")
    sp.add_argument("--repo", default=".")
    sp.add_argument("--since", help="Start tag/commit")

    args = p.parse_args()
    if not args.cmd:
        p.print_help()
        sys.exit(1)
    {"generate": cmd_generate, "tags": cmd_tags, "stats": cmd_stats}[args.cmd](args)


if __name__ == "__main__":
    main()
