#!/usr/bin/env bash
# WP3 -- fault-injection campaign over the WP2 family.
#   1. validate the measurement oracle (ld_exec) against the paper's RQ1 reference
#      traces and the WP2 expected labels;
#   2. run the campaign and (re)write RESULTS.md.
# Pure Python (the canonical oracle is rung6/differential.py under K, unavailable
# in the authoring env; ld_exec is validated so its numbers are trustworthy).
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
echo ">> validating the ld_exec oracle:"
python3 "$here/validate_exec.py"
echo; echo ">> running the mutation campaign:"
python3 "$here/mutate_campaign.py" >/dev/null && echo "   wrote RESULTS.md"
grep -A9 "## Per-operator detection" "$here/RESULTS.md" | tail -8
