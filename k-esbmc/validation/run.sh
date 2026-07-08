#!/usr/bin/env bash
# Dynamic ground-truth check: run OpenPLC/MATIEC's reference FB bodies and diff
# against K-ESBMC. Extracts the MATIEC lib/C headers from the OpenPLC container at
# runtime (so we don't redistribute GPL sources), compiles matiec_ref.c against
# them, and prints the executed Q traces. Compare with `make d-test-*` in ../.
#
# Requires Docker. Usage:  bash run.sh
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
img="${OPENPLC_IMAGE:-tuttas/openplc_v3:latest}"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

echo ">> extracting MATIEC lib/C from $img ..."
cid="$(docker create --platform linux/amd64 "$img")"
docker cp "$cid:/root/OpenPLC_v3/utils/matiec_src/lib/C/." "$work/" >/dev/null
docker rm "$cid" >/dev/null
cp "$here/matiec_ref.c" "$work/"

echo ">> compiling + running the reference FBs (executed OpenPLC semantics):"
docker run --rm --platform linux/amd64 -v "$work":/w -w /w gcc:13 \
  bash -lc 'gcc -std=gnu99 -w matiec_ref.c -o matiec_ref -lm && ./matiec_ref'

cat <<'EOF'

>> Expected K-ESBMC traces (from ../Makefile d-test-*), for comparison:
   TON: F,F,F,T,F     TOF: T,T,T,T,T,F     TP:  F,T,T,T,F,T
   CTU: F,F,F,F,T,F,F CTD: F,F,F,F,T,T,F
EOF
