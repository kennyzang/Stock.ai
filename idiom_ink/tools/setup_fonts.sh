#!/usr/bin/env bash
# Install the series fonts into ~/.fonts/idiom_ink (idempotent). Both are SIL OFL.
#   LXGW WenKai (Chinese, replaces KaiTi) · Selawik (English, Segoe-UI-metric-compatible)
# DejaVu Sans (pinyin tone marks) is usually preinstalled.
set -euo pipefail
D="$HOME/.fonts/idiom_ink"
mkdir -p "$D"
if [ ! -s "$D/LXGWWenKai-Medium.ttf" ]; then
  curl -fsSL -m 300 -o "$D/LXGWWenKai-Medium.ttf" \
    https://github.com/lxgw/LxgwWenKai/releases/download/v1.520/LXGWWenKai-Medium.ttf
fi
if [ ! -s "$D/selawkb.ttf" ]; then
  T=$(mktemp -d)
  curl -fsSL -m 120 -o "$T/sel.zip" https://github.com/microsoft/Selawik/releases/latest/download/Selawik_Release.zip
  python3 -I -c "import zipfile,sys; z=zipfile.ZipFile(sys.argv[1]); [z.extract(n, sys.argv[2]) for n in z.namelist() if n.endswith('.ttf')]" "$T/sel.zip" "$D"
fi
fc-cache -f "$HOME/.fonts" >/dev/null 2>&1 || true
fc-list | grep -i -E 'wenkai|selawik' | sed 's/^/installed: /' | head -6
