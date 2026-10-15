#!/usr/bin/env python3
"""SocialEcho uploader/scheduler for Idiom Ink (see HANDOVER_SOCIALECHO.md).

Auth: in cloud sessions the environment's proxy injects `Authorization` for api.socialecho.net,
so no key is handled here. (Elsewhere set SOCIALECHO_KEY and it is sent as a Bearer header.)
Every call costs team points; each response's remaining balance is printed.

Usage:
  socialecho.py points                           GET /v1/team (1 point) and print remaining points
  socialecho.py post VIDEO.mp4 CAPTION.txt WHEN  upload + create a scheduled post.
                                                 WHEN = ISO time with timezone, e.g. 2026-10-17T03:12:00+00:00
  socialecho.py posts [page]                     GET /v1/article (post list / statuses)
Never re-run `post` for the same video after an error without checking `posts` first (no double posts).
"""
import json, os, ssl, sys, urllib.parse, urllib.request

API = "https://api.socialecho.net"
ACCOUNT_ID = 22788134  # "Idiom Ink | Chinese Idioms" TikTok
CA = "/root/.ccr/ca-bundle.crt"
CTX = ssl.create_default_context(cafile=CA) if os.path.exists(CA) else None


def req(method, path, body=None):
    h = {"X-Lang": "en", "Content-Type": "application/json"}
    if os.environ.get("SOCIALECHO_KEY"):
        h["Authorization"] = "Bearer " + os.environ["SOCIALECHO_KEY"]
    r = urllib.request.Request(API + path, method=method, headers=h,
                               data=json.dumps(body).encode() if body is not None else None)
    try:
        with urllib.request.urlopen(r, context=CTX, timeout=120) as resp:
            status, data = resp.status, json.load(resp)
    except urllib.error.HTTPError as e:
        status, data = e.code, json.loads(e.read() or b"{}")
    left = ((data.get("meta") or {}).get("ai_points") or {}).get("remaining")
    print(f"[{method} {path.split('?')[0]}] http={status} code={data.get('code')} points_left={left} "
          f"request_id={data.get('request_id')} msg={data.get('message')}", file=sys.stderr)
    if not (200 <= status < 300 and data.get("code") == 0):
        raise SystemExit(f"SocialEcho call failed: {json.dumps(data, ensure_ascii=False)}")
    return data


def post(video, caption_file, when):
    caption = open(caption_file, encoding="utf-8").read().strip()
    if len(caption.encode("utf-16-le")) // 2 > 2200:
        raise SystemExit("caption over 2,200 UTF-16 units")
    name = os.path.basename(video)
    up = req("GET", "/v1/upload/url?" + urllib.parse.urlencode({"content_type": "video/mp4", "title": name}))["data"]
    with open(video, "rb") as f:
        put = urllib.request.Request(up["upload_url"], data=f.read(), method=up.get("method", "PUT"),
                                     headers=up.get("headers") or {"Content-Type": "video/mp4"})
    with urllib.request.urlopen(put, context=CTX, timeout=900) as r:
        if not 200 <= r.status < 300:
            raise SystemExit(f"upload PUT failed: http {r.status}")
    body = {"account_id": ACCOUNT_ID, "type": "video", "status": 1, "content": caption,
            "scheduled_at": when,
            "extra": {"draft": False, "is_ai_generated": True},  # AI label is required on every post
            "attachments": [{"url": up["public_url"]}], "comment": []}
    d = req("POST", "/v1/publish/article", body)
    print(json.dumps({"video": name, "record_id": d["data"]["id"], "request_id": d.get("request_id"),
                      "scheduled_at": when, "message": d.get("message")}, ensure_ascii=False))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "points":
        req("GET", "/v1/team")
    elif cmd == "post":
        post(*sys.argv[2:5])
    elif cmd == "posts":
        print(json.dumps(req("GET", "/v1/article?page=" + (sys.argv[2] if len(sys.argv) > 2 else "1"))["data"],
                         ensure_ascii=False, indent=1))
