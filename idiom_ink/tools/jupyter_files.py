#!/usr/bin/env python3
"""Copy files to/from the GPU server through the Jupyter contents API.

Env: JUPYTER_URL, JUPYTER_TOKEN (see `compshare.py jupyter`).
Usage:
  jupyter_files.py get /abs/remote/path local_path
  jupyter_files.py put local_path /abs/remote/path
Paths on the server are absolute (the Jupyter root is `/`). Fine for files up to a few hundred MB.
"""
import base64, json, os, ssl, sys, time, urllib.parse, urllib.request

URL = os.environ["JUPYTER_URL"].rstrip("/")
HDR = {"Authorization": f"token {os.environ['JUPYTER_TOKEN']}", "Content-Type": "application/json"}
CTX = ssl.create_default_context(cafile="/root/.ccr/ca-bundle.crt")


def _api(path):
    return f"{URL}/api/contents/{urllib.parse.quote(path.lstrip('/'))}"


def get(remote, local):
    # cache-buster: a re-read of a changed file once returned the stale copy
    req = urllib.request.Request(_api(remote) + f"?type=file&format=base64&content=1&_={time.time_ns()}", headers=HDR)
    with urllib.request.urlopen(req, context=CTX, timeout=900) as r:
        data = json.load(r)
    os.makedirs(os.path.dirname(os.path.abspath(local)), exist_ok=True)
    with open(local, "wb") as f:
        f.write(base64.b64decode(data["content"]))
    print(f"got {remote} -> {local} ({os.path.getsize(local)} bytes)")


def put(local, remote):
    with open(local, "rb") as f:
        body = {"type": "file", "format": "base64", "content": base64.b64encode(f.read()).decode()}
    req = urllib.request.Request(_api(remote), data=json.dumps(body).encode(), headers=HDR, method="PUT")
    with urllib.request.urlopen(req, context=CTX, timeout=900) as r:
        r.read()
    print(f"put {local} -> {remote} ({os.path.getsize(local)} bytes)")


if __name__ == "__main__":
    {"get": get, "put": put}[sys.argv[1]](sys.argv[2], sys.argv[3])
