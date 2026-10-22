# -*- coding: utf-8 -*-
r"""
INDEPENDENT checker for Rado-number colorings (certificates).
Does NOT import anything from rado_c1.py on purpose: it uses the plainest possible
definition so that a bug in the CNF generator cannot hide here.

A certificate is a JSON file:
  {"a": 2, "b": 3, "k": 4, "n": 226, "coloring": [c1, c2, ..., cn]}   (colors 0..k-1; coloring[j-1] = color of j)
It proves  R_k(a(x-y)=bz) > n  iff no (x, y, z) with 1 <= x,y,z <= n,  a*(x-y) == b*z  is monochromatic.
(x, y, z need not be distinct.)

Usage:  python tools/rado_verify.py results/c1/cert_....json
Exit code 0 = valid, 1 = invalid / malformed.
"""
import json, sys


def check(a, b, k, n, col):
    if len(col) != n:
        return False, f"coloring length {len(col)} != n {n}"
    if any((not isinstance(c, int)) or c < 0 or c >= k for c in col):
        return False, "color out of range"
    # plain triple loop on purpose (slow but obviously correct)
    for x in range(1, n + 1):
        for y in range(1, n + 1):
            if col[x - 1] != col[y - 1]:
                continue
            for z in range(1, n + 1):
                if a * (x - y) == b * z and col[z - 1] == col[x - 1]:
                    return False, f"monochromatic solution x={x} y={y} z={z} color={col[x-1]}"
    return True, "ok"


def main():
    if len(sys.argv) != 2:
        print(__doc__); sys.exit(1)
    d = json.load(open(sys.argv[1], encoding="utf-8"))
    ok, msg = check(d["a"], d["b"], d["k"], d["n"], d["coloring"])
    print(("VALID  " if ok else "INVALID ") + f"a={d['a']} b={d['b']} k={d['k']} n={d['n']}: {msg}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
