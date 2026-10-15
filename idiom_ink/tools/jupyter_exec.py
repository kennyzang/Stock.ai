#!/usr/bin/env python3
"""Run a shell command on the GPU server through its JupyterLab terminal API.

Cloud sessions cannot SSH to the server (raw TCP is blocked by the egress proxy),
but HTTPS/WebSocket to JupyterLab works.

Needs env vars (set in the cloud environment settings, never in git):
  JUPYTER_URL    e.g. https://8888-<pod>.pod.compshare.cn   (no trailing slash)
  JUPYTER_TOKEN  the Jupyter server token

Usage:
  jupyter_exec.py 'command' [timeout_seconds]     prints output, exits with the command's status
Long jobs: start them with `setsid nohup ... &` and poll, a terminal can drop.
Files: use the Jupyter contents API (GET/PUT $JUPYTER_URL/api/contents/<path>).
"""
import json, os, re, sys, time, urllib.parse, urllib.request, uuid

import websocket  # pip install websocket-client

URL = os.environ["JUPYTER_URL"].rstrip("/")
TOKEN = os.environ["JUPYTER_TOKEN"]
HOST = urllib.parse.urlparse(URL).netloc
CA = "/root/.ccr/ca-bundle.crt"
HDR = {"Authorization": f"token {TOKEN}"}
ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]|\x1b\][^\x07]*\x07")


def api(method, path):
    req = urllib.request.Request(f"{URL}{path}", method=method, headers=HDR, data=b"" if method == "POST" else None)
    import ssl
    with urllib.request.urlopen(req, context=ssl.create_default_context(cafile=CA), timeout=60) as r:
        body = r.read()
    return json.loads(body) if body else None


def run(cmd, timeout=300):
    name = api("POST", "/api/terminals")["name"]
    proxy = urllib.parse.urlparse(os.environ.get("HTTPS_PROXY", ""))
    kw = dict(http_proxy_host=proxy.hostname, http_proxy_port=proxy.port, proxy_type="http") if proxy.hostname else {}
    ws = websocket.create_connection(f"wss://{HOST}/terminals/websocket/{name}?token={TOKEN}",
                                     sslopt={"ca_certs": CA}, timeout=timeout, **kw)
    mark = uuid.uuid4().hex[:12]
    begin, end = f"__BEGIN_{mark}", f"__END_{mark}_"
    # The quotes split the markers, so the terminal's echo of this line never matches them.
    ws.send(json.dumps(["stdin", f"stty -echo; echo __BEGIN''_{mark}; {cmd}\n__rc=$?; echo; echo __END''_{mark}_$__rc\n"]))
    out, code, deadline = "", None, time.time() + timeout
    try:
        while time.time() < deadline:
            msg = json.loads(ws.recv())
            if msg[0] != "stdout":
                continue
            out += msg[1]
            clean = ANSI.sub("", out.replace("\r", ""))
            if end in clean:
                body, tail = clean.split(end, 1)
                body = body.split(begin, 1)[-1].lstrip("\n")
                # drop the shell prompt printed between the two input lines
                body = "\n".join(l for l in body.split("\n") if not re.match(r"^(\(\w+\) )?\S+@\S+:.*[#$] ?$", l))
                code = tail.split()[0] if tail.split() else "1"
                return body, int(code) if code.isdigit() else 1
    finally:
        ws.close()
        try:
            api("DELETE", f"/api/terminals/{name}")
        except Exception:
            pass
    return ANSI.sub("", out) + "\n[timed out]", 124


if __name__ == "__main__":
    text, rc = run(sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else 300)
    print(text, end="")
    sys.exit(rc)
