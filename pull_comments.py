"""Print all comments from the Supabase comment box (reads the public URL/key from comments.js).

Usage:  python pull_comments.py          → readable list
        python pull_comments.py --json   → raw JSON
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

src = (Path(__file__).parent / "comments.js").read_text(encoding="utf-8")
url = re.search(r'url:\s*"([^"]*)"', src).group(1).rstrip("/")
key = re.search(r'key:\s*"([^"]*)"', src).group(1)
if not url or not key:
    sys.exit("comments.js has no Supabase url/key yet.")

headers = {"apikey": key}
if not key.startswith("sb_"):
    headers["Authorization"] = "Bearer " + key
req = urllib.request.Request(f"{url}/rest/v1/comments?select=*&order=created_at.asc", headers=headers)
with urllib.request.urlopen(req, timeout=20) as r:
    rows = json.load(r)

if "--json" in sys.argv:
    print(json.dumps(rows, ensure_ascii=False, indent=1))
else:
    print(f"{len(rows)} comment(s)\n")
    for c in rows:
        where = f" @ ({c['x']:.2f}, {c['y']:.2f}{', h ' + format(c['z'], '.2f') if c.get('z') is not None else ''})" if c.get("x") is not None else ""
        print(f"#{c['id']} {c['created_at'][:16]} [{c['page']}] {c.get('name') or 'Anonymous'}{where}"
              f"{'  · layout: ' + c['layout'] if c.get('layout') else ''}\n  {c['body']}\n")
