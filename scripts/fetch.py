#!/usr/bin/env python3
"""Pulls public profile data from the GitHub REST API into data.json (stdlib only).

Uses GITHUB_TOKEN / GH_TOKEN when present (Actions), else the `gh` CLI token, else anonymous.
"""
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
    body, headers = get(f"/repos/{USER}/{repo}/commits?per_page=1", want_headers=True)
    if not body:
        return 0
    m = re.search(r'[?&]page=(\d+)>; rel="last"', headers.get("Link", ""))
    return int(m.group(1)) if m else len(body)


def main():
    user = get(f"/users/{USER}")
    repos = []
    for r in get(f"/users/{USER}/repos?per_page=100&sort=created"):
        if r["fork"]:
            continue
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
    data = {
        "created": user["created_at"][:10],
        "followers": user["followers"],
        "following": user["following"],
        "repos": repos,
    }
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "data.json")
    with open(out, "w") as fh:
        json.dump(data, fh, indent=2)
    print(f"wrote {out}: {len(repos)} repos, {sum(r['commits'] for r in repos)} commits")


if __name__ == "__main__":
    main()
