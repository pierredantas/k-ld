#!/usr/bin/env bash
# WP1a, executed end-to-end with the REAL toolchain (no Docker):
#   real MATIEC iec2c  --compile-->  C  --real CBMC-->  SAFE / VIOLATED
#
# Demonstrates the WP1a mechanism on genuine MATIEC-generated C:
#   * faithful scan-TON  -> property A proved SAFE   (MATIEC+CBMC sides with K-LD)
#   * havoc timer        -> property A VIOLATED      (the ESBMC false alarm)
#
# NOTE ON THE STANDARD LIBRARY. A locally-built iec2c (bison 3.x) does not load
# matiec's standard-FB library, so the library `TON` (wall-clock) is unavailable
# here; we express the timer as the equivalent scan-counting state machine in ST
# -- the exact faithful semantics K-LD implements. The library-`TON` path is what
# ../run_wp1a.sh exercises via the OpenPLC container, whose iec2c loads the lib.
#
# Requires: cbmc (brew install cbmc) and a built matiec iec2c.
#   MATIEC=/path/to/matiec  bash reproduce.sh
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
M="${MATIEC:?set MATIEC=/path/to/built/matiec (contains ./iec2c and ./lib)}"
command -v cbmc >/dev/null || { echo "need cbmc (brew install cbmc)"; exit 1; }

run_case () {  # <name> <st> <harness> <expected>
  local name="$1" st="$2" harness="$3" expect="$4"
  local w; w="$(mktemp -d)"; cp "$here/$st" "$w/prog.st"; cp "$here/$harness" "$w/harness.c"
  ( cd "$w"
    "$M/iec2c" -I "$M/lib" prog.st >/dev/null 2>&1
    printf '#include "res.c"\n#include "config.c"\n' > all.c
    printf '  %-9s : ' "$name"
    { cbmc harness.c all.c -I "$M/lib/C" --unwind 8 --no-unwinding-assertions 2>&1 || true; } \
      | grep -E "prop A|VERIFICATION (SUCCESSFUL|FAILED)" | tr '\n' ' '
    echo "   [expected: $expect]" )
  rm -rf "$w"
}

echo ">> WP1a on real MATIEC-generated C, checked by real CBMC:"
run_case faithful timer_faithful.st harness_faithful.c "prop A SUCCESS"
run_case havoc    timer_havoc.st    harness_havoc.c    "prop A FAILURE"
