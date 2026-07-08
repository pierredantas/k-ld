#!/usr/bin/env bash
# WP1b -- an independent verification ENGINE (NuSMV, BDD symbolic model checking)
# cross-checks the differential's timer disagreement, on the Btn->TON->Light probe.
#
#   faithful scan-TON -> invariant (Light -> Btn) is TRUE   (proved, UNBOUNDED)
#   havoc timer       -> invariant (Light -> Btn) is FALSE  (counterexample)
#
# NuSMV's BDD fixpoint is a fundamentally different algorithm from ESBMC's SMT-BMC
# and CBMC's SAT-BMC, and its proof is unbounded -- so a TRUE result here is a
# complete proof over all reachable states, not safe-up-to-horizon. Three engines
# (K-ESBMC reachability, MATIEC-C+CBMC, NuSMV BDD) now agree against ESBMC.
#
# SCOPE (honest): this is an independent *engine*, not an independent *front-end* --
# we author the SMV model, so it does not test another tool's timer handling the
# way a third-party LD verifier would. See PLCVERIF.md for why the intended
# independent-front-end tool (PLCverif) could not be used.
#
# Requires NuSMV (open source): https://nusmv.fbk.eu/  -> set NUSMV=/path/to/NuSMV
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
NUSMV="${NUSMV:?set NUSMV=/path/to/NuSMV (https://nusmv.fbk.eu/distrib/)}"

echo ">> WP1b: NuSMV (BDD symbolic) on the timer probe"
printf "  faithful : "; "$NUSMV" "$here/faithful.smv" 2>&1 | grep -iE "invariant.*is (true|false)" | tr -d '\n'; echo "   [expected: is true]"
printf "  havoc    : "; "$NUSMV" "$here/havoc.smv"    2>&1 | grep -iE "invariant.*is (true|false)" | tr -d '\n'; echo "   [expected: is false]"
