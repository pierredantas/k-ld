#!/usr/bin/env bash
# WP1a -- MATIEC-C + CBMC as an independent second verifier for the differential.
#
# WHY: the paper's differential rests on a single verifier (ESBMC-PLC) whose
# LD->GOTO front-end is from the authors' own line. This adds a SECOND, fully
# independent verification path over the same benchmarks:
#
#     PLCopen XML --[MATIEC: iec2c]--> C --[CBMC]--> SAFE / VIOLATED
#
# MATIEC's LD->C lowering is different from BOTH ESBMC-PLC's LD->GOTO AND K-ESBMC's
# plcopen2kld.py, so agreement/disagreement here is a genuinely independent
# second opinion. On the three known disagreements this path is expected to side
# with K-ESBMC (MATIEC models timers faithfully), turning "our oracle says so" into
# "an independent MATIEC+CBMC engine says so too".
#
# It reuses the exact container the RQ1 validation already pulls MATIEC from
# (see ../validation/run.sh), so it introduces no new trusted component.
#
# Requires: Docker. Usage:
#     bash run_wp1a.sh <program.xml> <program.json> <props.yaml> [unwind]
#
# NOTE ON SCOPE: the .ld files vendored in ../rung6 are already K-ESBMC DSL; this
# script needs the ORIGINAL PLCopen XML that ESBMC consumes (from the ESBMC-PLC
# benchmark repo). The one manual integration step is bindings.h -- mapping
# VAR(x) onto the MATIEC located-variable symbol for x (see below).
set -euo pipefail

XML="${1:?need program.xml}"; JSON="${2:?need program.json}"; PROPS="${3:?need props.yaml}"
UNWIND="${4:-8}"
img="${OPENPLC_IMAGE:-tuttas/openplc_v3:latest}"
here="$(cd "$(dirname "$0")" && pwd)"
work="$(mktemp -d)"; trap 'rm -rf "$work"' EXIT
cp "$XML" "$work/prog.xml"

echo ">> [1/4] compiling PLCopen XML -> C with MATIEC (iec2c) inside $img ..."
# OpenPLC ships iec2c (built) and the matiec runtime lib under utils/matiec_src.
# For a graphical LD body, iec2c is driven on the ST that OpenPLC's editor
# generates; OpenPLC's own build script (compile_program.sh) performs that
# XML->ST->C step. We invoke it and collect the generated C (POUS.*, Res0.c,
# Config0.c, LOCATED_VARIABLES.h).
docker run --rm --platform linux/amd64 -v "$work":/w -w /w "$img" bash -lc '
  set -e
  OP=/root/OpenPLC_v3
  cp prog.xml "$OP/webserver/st_files/prog.xml"
  # Reuse OpenPLC'\''s compile path (XML -> ST -> iec2c -> C):
  cd "$OP/webserver/scripts"
  ./compile_program.sh prog.xml >/w/compile.log 2>&1 || { cat /w/compile.log; exit 1; }
  cp "$OP/webserver/core"/{POUS.c,POUS.h,Res0.c,Config0.c,LOCATED_VARIABLES.h,Config0.h} /w/ 2>/dev/null || true
  cp "$OP/utils/matiec_src/lib/C/"*.h /w/ 2>/dev/null || true
'
echo "   generated: $(cd "$work" && ls *.c *.h 2>/dev/null | tr '\n' ' ')"

echo ">> [2/4] generating verifier-independent CBMC harness from props ..."
python3 "$here/gen_cbmc_harness.py" "$JSON" "$PROPS" --scans "$UNWIND" > "$work/harness.c"

echo ">> [3/4] bindings.h (VAR(x) -> MATIEC located symbol) ..."
if [ -f "$here/bindings/$(basename "$XML" .xml).h" ]; then
  cp "$here/bindings/$(basename "$XML" .xml).h" "$work/bindings.h"
  echo "   using checked-in bindings for $(basename "$XML")"
else
  # Auto-stub from LOCATED_VARIABLES.h; MATIEC names located vars __IX0_0 etc.
  # This stub is the one place a human confirms the input/output symbol map.
  python3 "$here/gen_bindings_stub.py" "$JSON" "$work/LOCATED_VARIABLES.h" "$work/prog.xml" "$PROPS" > "$work/bindings.h" || {
    echo "!! could not auto-generate bindings.h -- write $here/bindings/$(basename "$XML" .xml).h by hand"; exit 2; }
  echo "   auto-stubbed bindings.h (REVIEW the located-variable map before trusting a verdict)"
  if grep -q "UNRESOLVED" "$work/bindings.h"; then
    echo "!! bindings.h has UNRESOLVED symbols (locals referenced by properties) -- complete them before the run:"
    sed -n '/UNRESOLVED: complete/,/---/p' "$work/bindings.h"; exit 3
  fi
fi

echo ">> [4/4] running CBMC over MATIEC-generated C ..."
docker run --rm --platform linux/amd64 -v "$work":/w -w /w "$img" bash -lc "
  command -v cbmc >/dev/null || { apt-get update -qq && apt-get install -y -qq cbmc >/dev/null; }
  cbmc harness.c Res0.c Config0.c POUS.c --unwind $((UNWIND+1)) --no-unwinding-assertions \
       --function main 2>&1 | tee /w/cbmc.log
"
echo
if grep -q "VERIFICATION FAILED" "$work/cbmc.log"; then echo "RESULT: VIOLATED (MATIEC-C+CBMC)"
elif grep -q "VERIFICATION SUCCESSFUL" "$work/cbmc.log"; then echo "RESULT: SAFE (MATIEC-C+CBMC)"
else echo "RESULT: inconclusive -- inspect $work/cbmc.log"; fi
