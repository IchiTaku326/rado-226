# -*- coding: utf-8 -*-
r"""
Rado numbers R_k(a(x-y)=bz) by SAT.  Building block of the C1 search (see c1_search.py).

Definition used (same as Chang-De Loera-Wesley, arXiv:2210.03262, as far as we could read it):
  R_k(E) = smallest n such that every k-coloring of {1..n} has a monochromatic positive solution
  (x, y, z in {1..n}, not necessarily distinct) of E.   Here E:  a*(x-y) = b*z.

Sub-commands
  gen     write a DIMACS CNF
  solve   solve one instance (one seed) and print ONE json line; saves a certificate if SAT
  rvalue  find R by increasing n (for reproducing known values; small cases only)

Backends: pysat (pip install python-sat; works on Windows), cadical / kissat (external binaries).
Diversification: --seed permutes variable names, clause order and literal order.
"""
import argparse, json, os, random, subprocess, sys, tempfile, time
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))


def now():
    return datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")


def solutions(a, b, n):
    sols = set()
    for x in range(2, n + 1):
        for y in range(1, x):
            t = a * (x - y)
            if t % b == 0:
                z = t // b
                if 1 <= z <= n:
                    sols.add(frozenset((x, y, z)))
    return sols


def build_cnf(a, b, k, n, symbreak=True):
    def v(j, c):
        return (j - 1) * k + c + 1
    base = n * k

    def u(j, c):  # "color c is used somewhere in 1..j", c in 0..k-2
        return base + (j - 1) * (k - 1) + c + 1
    cl = []
    for j in range(1, n + 1):
        cl.append([v(j, c) for c in range(k)])
        for c1 in range(k):
            for c2 in range(c1 + 1, k):
                cl.append([-v(j, c1), -v(j, c2)])
    for S in solutions(a, b, n):
        for c in range(k):
            cl.append([-v(j, c) for j in sorted(S)])
    nvars = base
    if symbreak and k > 1:
        nvars = base + n * (k - 1)
        for j in range(1, n + 1):
            for c in range(k - 1):
                cl.append([-v(j, c), u(j, c)])
                if j > 1:
                    cl.append([-u(j - 1, c), u(j, c)])
                    cl.append([-u(j, c), u(j - 1, c), v(j, c)])
                else:
                    cl.append([-u(j, c), v(j, c)])
            for c in range(1, k):
                if j == 1:
                    cl.append([-v(1, c)])
                else:
                    cl.append([-v(j, c), u(j - 1, c - 1)])
    return cl, nvars, v


def permute(cl, nvars, seed):
    if seed == 0:
        return cl, list(range(nvars + 1))
    rng = random.Random(seed)
    p = list(range(1, nvars + 1))
    rng.shuffle(p)
    mp = [0] + p                      # old var -> new var
    out = [[(mp[abs(l)] if l > 0 else -mp[abs(l)]) for l in c] for c in cl]
    for c in out:
        rng.shuffle(c)
    rng.shuffle(out)
    return out, mp


def write_dimacs(path, cl, nvars):
    with open(path, "w") as f:
        f.write(f"p cnf {nvars} {len(cl)}\n")
        for c in cl:
            f.write(" ".join(map(str, c)) + " 0\n")


def run_backend(cl, nvars, backend, binpath, timeout, proof=None):
    """returns (status, model_dict or None).  status in SAT / UNSAT / TIMEOUT / ERROR"""
    if backend == "pysat":
        from pysat.solvers import Cadical153
        with Cadical153(bootstrap_with=cl) as s:
            if s.solve():
                m = s.get_model()
                return "SAT", {abs(l): (l > 0) for l in m}
            return "UNSAT", None
    fd, path = tempfile.mkstemp(suffix=".cnf")
    os.close(fd)
    try:
        write_dimacs(path, cl, nvars)
        cmd = [binpath, "-q"] if backend == "kissat" else [binpath, "-q"]
        cmd.append(path)
        if proof:
            cmd.append(proof)
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return "TIMEOUT", None
        model = {}
        status = None
        for line in p.stdout.splitlines():
            if line.startswith("s SATISFIABLE"):
                status = "SAT"
            elif line.startswith("s UNSATISFIABLE"):
                status = "UNSAT"
            elif line.startswith("v "):
                for tok in line[2:].split():
                    t = int(tok)
                    if t != 0:
                        model[abs(t)] = t > 0
        if status is None:
            return "ERROR", None
        return status, (model if status == "SAT" else None)
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def solve_instance(a, b, k, n, seed, backend, binpath, timeout, outdir, proof=None):
    t0 = time.time()
    cl, nvars, v = build_cnf(a, b, k, n)
    pcl, mp = permute(cl, nvars, seed)
    status, model = run_backend(pcl, nvars, backend, binpath, timeout, proof)
    res = {"jst_time": now(), "a": a, "b": b, "k": k, "n": n, "seed": seed, "backend": backend,
           "status": status, "seconds": round(time.time() - t0, 2), "cert": ""}
    if status == "SAT":
        col = []
        for j in range(1, n + 1):
            cs = [c for c in range(k) if model.get(mp[v(j, c)], False)]
            if len(cs) != 1:
                res["status"] = "ERROR"; res["note"] = "bad model"
                return res
            col.append(cs[0])
        os.makedirs(outdir, exist_ok=True)
        cert = os.path.join(outdir, f"cert_a{a}_b{b}_k{k}_n{n}_seed{seed}.json")
        tmp = cert + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"a": a, "b": b, "k": k, "n": n, "seed": seed, "backend": backend,
                       "jst_time": res["jst_time"], "coloring": col}, f)
            f.flush(); os.fsync(f.fileno())
        os.replace(tmp, cert)
        # independent verification (separate file, separate code path)
        here = os.path.dirname(os.path.abspath(__file__))
        vp = subprocess.run([sys.executable, os.path.join(here, "rado_verify.py"), cert],
                            capture_output=True, text=True)
        if vp.returncode != 0:
            res["status"] = "ERROR"; res["note"] = "verification failed: " + vp.stdout.strip()
        else:
            res["cert"] = cert
    return res


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("gen", "solve", "rvalue"):
        p = sub.add_parser(name)
        p.add_argument("--a", type=int, required=True)
        p.add_argument("--b", type=int, required=True)
        p.add_argument("--k", type=int, required=True)
        if name != "rvalue":
            p.add_argument("--n", type=int, required=True)
        if name == "rvalue":
            p.add_argument("--start", type=int, default=2)
            p.add_argument("--max-n", type=int, default=2000)
        if name == "gen":
            p.add_argument("--out", required=True)
        else:
            p.add_argument("--seed", type=int, default=0)
            p.add_argument("--backend", choices=["pysat", "cadical", "kissat"], default="pysat")
            p.add_argument("--bin", default="cadical")
            p.add_argument("--timeout", type=float, default=None)
            p.add_argument("--outdir", default=os.path.join("results", "c1"))
            p.add_argument("--proof", default=None, help="DRAT proof path (cadical/kissat binaries only)")
    a = ap.parse_args()
    if a.cmd == "gen":
        cl, nv, _ = build_cnf(a.a, a.b, a.k, a.n)
        write_dimacs(a.out, cl, nv)
        print(f"wrote {a.out}: vars={nv} clauses={len(cl)}")
    elif a.cmd == "solve":
        r = solve_instance(a.a, a.b, a.k, a.n, a.seed, a.backend, a.bin, a.timeout, a.outdir, a.proof)
        print(json.dumps(r))
    else:
        n = a.start
        while n <= a.max_n:
            r = solve_instance(a.a, a.b, a.k, n, 0, a.backend, a.bin, a.timeout, a.outdir)
            print(f"[{r['jst_time']} JST] n={n} {r['status']} ({r['seconds']}s)", flush=True)
            if r["status"] == "UNSAT":
                print(f"R_{a.k}({a.a}(x-y)={a.b}z) = {n}")
                return
            if r["status"] != "SAT":
                print("stopped:", r); return
            n += 1
        print("max-n reached")


if __name__ == "__main__":
    main()
