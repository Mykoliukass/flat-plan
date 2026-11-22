"""Print all comments from the Supabase comment box (reads the public URL/key from comments.js).

Usage:  python pull_comments.py          → OPEN comments only (not marked done in comments-status.json)
        python pull_comments.py --all    → include handled ones
        python pull_comments.py --json   → raw JSON (open only unless --all)
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

status_file = Path(__file__).parent / "comments-status.json"
status = json.loads(status_file.read_text(encoding="utf-8")) if status_file.exists() else {}
done = {int(k) for k, v in status.items() if v.get("status") == "done"}
total = len(rows)
if "--all" not in sys.argv:
    rows = [c for c in rows if c["id"] not in done]

if "--json" in sys.argv:
    print(json.dumps(rows, ensure_ascii=False, indent=1))
else:
    print(f"{len(rows)} comment(s) shown  ({total} total, {len(done)} marked done)\n")
    for c in rows:
        where = f" @ ({c['x']:.2f}, {c['y']:.2f}{', h ' + format(c['z'], '.2f') if c.get('z') is not None else ''})" if c.get("x") is not None else ""
        mark = "  ✓ DONE: " + status[str(c["id"])].get("note", "") if c["id"] in done else ""
        print(f"#{c['id']} {c['created_at'][:16]} [{c['page']}] {c.get('name') or 'Anonymous'}{where}"
              f"{'  · layout: ' + c['layout'] if c.get('layout') else ''}{mark}\n  {c['body']}\n")
