#!/usr/bin/env python3
"""Pulls public profile data from the GitHub REST API into data.json (stdlib only).

Uses GITHUB_TOKEN / GH_TOKEN when present (Actions), else the `gh` CLI token, else anonymous.
"""
import base64
import datetime
import json
import os
import re
import subprocess
import sys
import urllib.request

USER = "mitaro-cs"
HERE = os.path.dirname(os.path.abspath(__file__))
API = "https://api.github.com"


def token():
    t = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if t:
        return t
    try:
        return subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=10).stdout.strip() or None
    except Exception:
        return None


TOKEN = token()


def get(path, want_headers=False):
    req = urllib.request.Request(path if path.startswith("http") else API + path,
                                 headers={"Accept": "application/vnd.github+json", "User-Agent": "profile-build"})
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = json.loads(r.read() or "null")
            return (body, dict(r.headers)) if want_headers else body
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return (None, {}) if want_headers else None
        raise


def commit_count(repo):
    body, headers = get(f"/repos/{USER}/{repo}/commits?per_page=1&author={USER}", want_headers=True)
    if not body:
        return 0
    m = re.search(r'[?&]page=(\d+)>; rel="last"', headers.get("Link", ""))
    return int(m.group(1)) if m else len(body)


def commit_list(repo):
    out, page = [], 1
    while True:
        batch = get(f"/repos/{USER}/{repo}/commits?author={USER}&per_page=100&page={page}") or []
        for c in batch:
            out.append({"repo": repo, "ts": c["commit"]["author"]["date"],
                        "msg": " ".join(c["commit"]["message"].split("\n")[0].split())})
        if len(batch) < 100:
            return out
        page += 1


PIN_NAMES = ("campus", "storagesystem")   # the pinned project; it was StorageSystem before the rename


def project_stats(paths, changelog):
    """What the pinned project is made of, from its file tree and changelog."""
    def count(pat):
        return sum(1 for p in paths if re.search(pat, p))
    migrations = [int(m) for p in paths for m in re.findall(r"/db/migration/V(\d+)__", p)]
    return {
        "java": count(r"^src/main/java/.+\.java$"),
        "svelte": count(r"\.svelte$"),
        "tests": count(r"^src/test/.+(Test|IT)\.java$") + count(r"\.spec\.ts$"),
        "migrations": max(migrations, default=0),
        "screens": count(r"^web/src/routes/.*\+page\.svelte$"),
        "versions": len(re.findall(r"^## \d", changelog, re.M)),
    }


def pin_stats(repo, branch, old):
    try:
        tree = get(f"/repos/{USER}/{repo}/git/trees/{branch}?recursive=1") or {}
        log = get(f"/repos/{USER}/{repo}/contents/CHANGELOG.md?ref={branch}") or {}
        changelog = base64.b64decode(log.get("content", "")).decode("utf-8", "replace")
        paths = [t["path"] for t in tree.get("tree", []) if t["type"] == "blob"]
        if not paths or tree.get("truncated"):
            return old
        return project_stats(paths, changelog)
    except Exception as e:                   # a failed call keeps the last good numbers on the card
        print(f"pinned stats skipped: {e}", file=sys.stderr)
        return old


def main():
    user = get(f"/users/{USER}")
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "data.json")
    try:
        prev = json.load(open(os.path.join(HERE, "data.json")))
    except (OSError, ValueError):
        prev = {}
    repos, pin = [], prev.get("pin")
    for r in get(f"/users/{USER}/repos?per_page=100&sort=created"):
        if r["fork"]:
            continue
        if r["name"].lower() in PIN_NAMES:
            pin = pin_stats(r["name"], r["default_branch"], pin)
        rel = get(f"/repos/{USER}/{r['name']}/releases/latest")
        repos.append({
            "name": r["name"],
            "created": r["created_at"][:10],
            "pushed": r["pushed_at"][:10],
            "stars": r["stargazers_count"],
            "langs": get(f"/repos/{USER}/{r['name']}/languages") or {},
            "commits": commit_count(r["name"]),
            "release": rel["tag_name"] if rel else None,
        })
    commits = sorted((c for r in repos if r["name"] != USER for c in commit_list(r["name"])),
                     key=lambda c: c["ts"], reverse=True)
    data = {
        "created": user["created_at"][:10],
        "followers": user["followers"],
        "following": user["following"],
        # changes once a week, so the workflow commits at least weekly and GitHub never marks the repo inactive
        "week": "{}-W{:02d}".format(*datetime.date.today().isocalendar()[:2]),
        "repos": repos,
        "pin": pin,
        "commits": commits,
    }
    with open(out, "w") as fh:
        json.dump(data, fh, indent=2)
    print(f"wrote {out}: {len(repos)} repos, {sum(r['commits'] for r in repos)} commits")


if __name__ == "__main__":
    main()
