#!/usr/bin/env bash
# Step 2 (proof check): every cube gets a CaDiCaL DRAT proof that drat-trim must accept.
# Needs Linux (or WSL), python3, and bin_linux/cadical + bin_linux/drat-trim (see bin_linux/README.md).
# Resumable: run again to continue. About 28 GB of proofs are written to a temporary folder and deleted again.
cd "$(dirname "$0")"
WORKERS="${WORKERS:-11}"
python3 tools/verify_proofs.py --workers "$WORKERS" --outdir results/proof_check_n226
cat results/proof_check_n226/FINAL.txt
