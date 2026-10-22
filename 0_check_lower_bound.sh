#!/usr/bin/env bash
# Check the lower bound: the given 4-colouring of 1..225 has no monochromatic solution of 2(x-y)=3z.
cd "$(dirname "$0")"
python3 tools/rado_verify.py results/lower_bound_n225/cert_a2_b3_k4_n225_seed5.json
