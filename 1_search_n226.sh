#!/usr/bin/env bash
# Step 1 (upper bound): cube-and-conquer search for n=226. Resumable: run again to continue.
# Needs: python3 and  pip install python-sat.   Change WORKERS to your number of cores (default 11).
cd "$(dirname "$0")"
WORKERS="${WORKERS:-11}"
python3 tools/cube_search.py --a 2 --b 3 --k 4 --n 226 --depth 10 --workers "$WORKERS" \
  --backend pysat --budget 20000 --outdir results/cube_search_n226
cat results/cube_search_n226/FINAL.txt
