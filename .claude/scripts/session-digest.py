#!/usr/bin/env python3
"""하루치 Claude Code 세션을 훑어 요약 재료를 뽑는다.

출력은 JSON. 에이전트가 이걸 읽고 raw/sessions/<date>.md 를 쓴다.
스크립트는 요약하지 않는다 — 기계가 할 수 있는 추출까지만.
"""
import json, sys, re, datetime, pathlib, collections

PROJECTS = pathlib.Path.home() / ".claude/projects"
# 이 vault 자신의 세션은 제외한다 (재귀 방지)
EXCLUDE_PROJECT_SUBSTR = ["Obsidian-Vault"]
MAX_PROMPT = 400


def text_of(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        out = []
        for b in content:
            if isinstance(b, dict) and b.get("type") == "text":
                out.append(b.get("text", ""))
        return "\n".join(out)
    return ""


def scan(path, day):
    """세션 파일 하나에서 그날의 메타와 발화를 뽑는다."""
    title = cwd = branch = None
    user_msgs, assistant_tail = [], []
    tools = set()
    stamps = []
    for line in path.open(encoding="utf-8"):
        try:
            d = json.loads(line)
        except Exception:
            continue
        t = d.get("type")
        if t == "custom-title":
            title = d.get("customTitle") or title
        elif t == "tools-used":
            for x in d.get("tools") or []:
                tools.add(x if isinstance(x, str) else str(x))
        if d.get("cwd"):
            cwd = d["cwd"]
        if d.get("gitBranch"):
            branch = d["gitBranch"]
        ts = d.get("timestamp")
        if not ts:
            continue
        date = ts[:10]
        if date != day:
            continue
        stamps.append(ts)
        if t == "user" and not d.get("isSidechain"):
            body = text_of((d.get("message") or {}).get("content"))
            body = re.sub(r"<[^>]+>.*?</[^>]+>", "", body, flags=re.S).strip()
            if body and not body.startswith("Caveat:"):
                user_msgs.append(body[:MAX_PROMPT])
        elif t == "assistant" and not d.get("isSidechain"):
            body = text_of((d.get("message") or {}).get("content")).strip()
            if body:
                assistant_tail.append(body[:MAX_PROMPT])
    if not stamps:
        return None
    return {
        "file": path.name,
        "project": path.parent.name,
        "title": title,
        "cwd": cwd,
        "branch": branch,
        "first_seen": min(stamps),
        "last_seen": max(stamps),
        "turns": len(user_msgs),
        "tools": sorted(tools)[:12],
        "user_prompts": user_msgs[:6],
        "assistant_last": assistant_tail[-2:] if assistant_tail else [],
    }


def main(argv):
    day = argv[1] if len(argv) > 1 else str(datetime.date.today())
    rows = []
    for proj in sorted(PROJECTS.iterdir()):
        if not proj.is_dir():
            continue
        if any(s in proj.name for s in EXCLUDE_PROJECT_SUBSTR):
            continue
        for f in proj.glob("*.jsonl"):
            r = scan(f, day)
            if r:
                rows.append(r)
    # resume 하면 같은 대화가 여러 jsonl로 갈라진다. (project, title)로 합친다.
    merged = {}
    for r in sorted(rows, key=lambda r: r["first_seen"]):
        key = (r["project"], r["title"] or r["file"])
        if key not in merged:
            merged[key] = r
            continue
        m = merged[key]
        m["turns"] += r["turns"]
        m["last_seen"] = max(m["last_seen"], r["last_seen"])
        m["branch"] = m["branch"] or r["branch"]
        for p_ in r["user_prompts"]:
            if p_ not in m["user_prompts"]:
                m["user_prompts"].append(p_)
        m["assistant_last"] = r["assistant_last"] or m["assistant_last"]
        m["tools"] = sorted(set(m["tools"]) | set(r["tools"]))[:12]
        m["parts"] = m.get("parts", 1) + 1
    rows = sorted(merged.values(), key=lambda r: r["first_seen"])
    by_proj = collections.Counter(r["project"] for r in rows)
    print(json.dumps({
        "date": day,
        "session_count": len(rows),
        "by_project": dict(by_proj),
        "sessions": rows,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
