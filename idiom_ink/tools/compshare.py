#!/usr/bin/env python3
"""Minimal CompShare (UCloud-style) API client: start / stop / describe the GPU instance.

Env: COMPSHARE_PUBLIC_KEY, COMPSHARE_PRIVATE_KEY (never commit them).
Signature = sha1( concat(sorted key+value pairs) + private_key ).

Usage:
  compshare.py call Action [Key=Value ...]   raw call, prints JSON
  compshare.py status                        state, GPU count, CPU, memory
  compshare.py start | stop                  start (with GPU) / stop the instance
  compshare.py wait STATE [timeout_s]        poll until State == STATE (Running / Stopped)
  compshare.py balance                       available account balance (CNY)
  compshare.py jupyter                       print `export JUPYTER_URL=... JUPYTER_TOKEN=...` (eval it)
The instance and its Jupyter token come from the API, so only the two keys are needed.
"""
import hashlib, json, os, ssl, sys, time, urllib.parse, urllib.request

API = "https://api.compshare.cn/"
CA = "/root/.ccr/ca-bundle.crt"
REGION, ZONE, HOST_ID = "cn-sh2", "cn-sh2-01", "cpod-1vrgybf1nkdu"


def _flat(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    return str(v)


def call(action, **params):
    p = {"Action": action, "PublicKey": os.environ["COMPSHARE_PUBLIC_KEY"], **params}
    raw = "".join(k + _flat(p[k]) for k in sorted(p)) + os.environ["COMPSHARE_PRIVATE_KEY"]
    p["Signature"] = hashlib.sha1(raw.encode()).hexdigest()
    req = urllib.request.Request(API, data=json.dumps(p).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    ctx = ssl.create_default_context(cafile=CA) if os.path.exists(CA) else None
    with urllib.request.urlopen(req, context=ctx, timeout=60) as r:
        return json.load(r)


def _ok(r):
    if r.get("RetCode") != 0:
        raise SystemExit(f"CompShare error {r.get('RetCode')}: {r.get('Message')}")
    return r


def host():
    r = _ok(call("DescribeCompShareInstance", Region=REGION, Zone=ZONE, **{"UHostIds.0": HOST_ID}))
    return r["UHostSet"][0]


def jupyter():
    h = host()
    urls = [s["URL"] for s in h.get("Softwares") or [] if s["Name"] == "JupyterLab"]
    if not urls:
        raise SystemExit(f"no JupyterLab URL (instance State={h['State']}; it is only listed while Running)")
    url = urls[0]
    u = urllib.parse.urlparse(url)
    return f"{u.scheme}://{u.netloc}", urllib.parse.parse_qs(u.query)["token"][0]


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "call":
        kv = dict(a.split("=", 1) for a in sys.argv[3:])
        print(json.dumps(call(sys.argv[2], **kv), ensure_ascii=False, indent=1))
    elif cmd == "status":
        h = host()
        print(f"{h['UHostId']} State={h['State']} GPU={h['GPU']}x{h['GpuType']} CPU={h['CPU']} Mem={h['Memory']}MB")
    elif cmd in ("start", "stop"):
        extra = {"WithoutGpu": False} if cmd == "start" else {}  # always start WITH the GPU
        action = "StartCompShareInstance" if cmd == "start" else "StopCompShareInstance"
        print(json.dumps(_ok(call(action, Region=REGION, Zone=ZONE, UHostId=HOST_ID, **extra))))
    elif cmd == "wait":
        want, limit = sys.argv[2], time.time() + float(sys.argv[3] if len(sys.argv) > 3 else 900)
        while (state := host()["State"]) != want:
            if time.time() > limit:
                raise SystemExit(f"timeout: still {state}")
            time.sleep(15)
        print(state)
    elif cmd == "balance":
        a = _ok(call("GetBalance"))["AccountInfo"]
        print(f"AmountAvailable={a['AmountAvailable']} Amount={a['Amount']} Credit={a['AmountCredit']}")
    elif cmd == "jupyter":
        url, tok = jupyter()
        print(f"export JUPYTER_URL={url} JUPYTER_TOKEN={tok}")
