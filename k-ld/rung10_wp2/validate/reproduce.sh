#!/usr/bin/env bash
# Independent NuSMV cross-check of the WP2 family's *expected verdicts*.
# K-LD (krun) is the primary oracle for the family; these NuSMV encodings are an
# independent confirmation that the labels in ../coverage.md are correct, across
# all three property kinds and both verdicts:
#   ton_chain2   (mutual_exclusion, safe)   -> invariant true
#   tof_hold     (invariant,        unsafe) -> invariant false
#   ctu_saturate (absence,          safe)   -> invariant true
# Requires NuSMV: https://nusmv.fbk.eu/  -> set NUSMV=/path/to/NuSMV
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
NUSMV="${NUSMV:?set NUSMV=/path/to/NuSMV}"
for m in ton_chain2 tof_hold ctu_saturate; do
  printf "  %-14s " "$m"
  "$NUSMV" "$here/$m.smv" 2>&1 | grep -iE "invariant.*is (true|false)" | tr -d '\n'; echo
done
