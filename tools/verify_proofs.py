# -*- coding: utf-8 -*-
r"""
Proof check of the n=226 cube-and-conquer result, cube by cube (run inside WSL / Linux):
   for every cube:  CNF(n) + unit clauses of the cube  --cadical-->  DRAT proof  --drat-trim-->  VERIFIED
Resumable: one CSV per worker (append, flush+fsync, JST time); cubes already VERIFIED are skipped on restart.
It also re-checks that the cube list is complete by brute force (4^depth colourings) and prints the count.
Usage (from the project folder, inside WSL):  python3 tools/verify_proofs.py --workers 11
"""
import argparse, csv, glob, itertools, os, shutil, subprocess, sys, tempfile, time
from datetime import datetime, timezone, timedelta
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cube_search import enum_cubes
from rado_c1 import build_cnf, write_dimacs, solutions

JST = timezone(timedelta(hours=9))
def now(): return datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")


def brute_cover(a, b, k, d):
    sols = [tuple(sorted(s)) for s in solutions(a, b, d)]
    cnt = 0
    for col in itertools.product(range(k), repeat=d):
        m = -1; ok = True
        for c in col:
            if c > m + 1: ok = False; break
            m = max(m, c)
        if not ok: continue
        if any(len(set(col[t - 1] for t in sol)) == 1 for sol in sols): continue
        cnt += 1
    return cnt


def verified_ids(outdir):
    ids = set()
    for f in glob.glob(os.path.join(outdir, "verify_w*.csv")):
        with open(f, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                if r["result"] == "VERIFIED": ids.add(int(r["cube"]))
    return ids


def worker(args, w):
    cubes = enum_cubes(args.a, args.b, args.k, args.depth)
    cl, nv, v = build_cnf(args.a, args.b, args.k, args.n)
    tmpd = tempfile.mkdtemp(prefix=f"vp{w}_")
    cad = os.path.join(args.bindir, "cadical"); drat = os.path.join(args.bindir, "drat-trim")
    path = os.path.join(args.outdir, f"verify_w{w}.csv")
    new = not os.path.exists(path)
    fh = open(path, "a", newline="", encoding="utf-8")
    wr = csv.DictWriter(fh, fieldnames=["jst_time", "cube", "result", "solve_s", "proof_bytes", "total_s"])
    if new: wr.writeheader(); fh.flush(); os.fsync(fh.fileno())
    done = verified_ids(args.outdir)
    for i in range(len(cubes)):
        if i % args.workers != w or i in done: continue
        cnf = os.path.join(tmpd, "c.cnf"); prf = os.path.join(tmpd, "c.drat")
        write_dimacs(cnf, cl + [[v(j + 1, c)] for j, c in enumerate(cubes[i])], nv)
        t0 = time.time()
        p = subprocess.run([cad, "-q", cnf, prf], capture_output=True, text=True)
        ts = time.time() - t0
        st = [l for l in p.stdout.splitlines() if l.startswith("s ")]
        if st and "UNSATISFIABLE" in st[0]:
            d = subprocess.run([drat, cnf, prf, "-t", "40000"], capture_output=True, text=True)
            res = "VERIFIED" if "s VERIFIED" in d.stdout else "NOTVERIFIED"
        else:
            res = "SOLVER_" + (st[0][2:] if st else "NONE").replace(" ", "_")
        wr.writerow({"jst_time": now(), "cube": i, "result": res, "solve_s": round(ts, 1),
                     "proof_bytes": os.path.getsize(prf) if os.path.exists(prf) else 0, "total_s": round(time.time() - t0, 1)})
        fh.flush(); os.fsync(fh.fileno())
        for f in (cnf, prf):
            try: os.remove(f)
            except OSError: pass
    shutil.rmtree(tmpd, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", type=int, default=2); ap.add_argument("--b", type=int, default=3)
    ap.add_argument("--k", type=int, default=4); ap.add_argument("--n", type=int, default=226)
    ap.add_argument("--depth", type=int, default=10)
    ap.add_argument("--workers", type=int, default=11)
    ap.add_argument("--bindir", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bin_linux"))
    ap.add_argument("--outdir", default=os.path.join("results", "proofcheck226"))
    ap.add_argument("--worker-id", type=int, default=None)
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    # binaries on /mnt/<drive> are often not executable: copy to a local temp dir
    local = os.path.join(tempfile.gettempdir(), "satbin")
    if a.worker_id is None:
        os.makedirs(local, exist_ok=True)
        for nme in ("cadical", "drat-trim"):
            shutil.copy(os.path.join(a.bindir, nme), os.path.join(local, nme)); os.chmod(os.path.join(local, nme), 0o755)
    a.bindir = local
    if a.worker_id is not None:
        worker(a, a.worker_id); return
    cubes = enum_cubes(a.a, a.b, a.k, a.depth)
    bc = brute_cover(a.a, a.b, a.k, a.depth)
    line = f"[{now()} JST] cubes in list={len(cubes)}; independent brute-force count of canonical solution-free prefixes={bc}; {'MATCH' if bc == len(cubes) else 'MISMATCH!'}"
    print(line, flush=True)
    with open(os.path.join(a.outdir, "FINAL.txt"), "a", encoding="utf-8") as f: f.write(line + "\n")
    ps = [subprocess.Popen([sys.executable, os.path.abspath(__file__)] + sys.argv[1:] + ["--worker-id", str(w)]) for w in range(a.workers)]
    last = 0
    try:
        while any(p.poll() is None for p in ps):
            time.sleep(5)
            if time.time() - last > 300:
                ok = len(verified_ids(a.outdir)); last = time.time()
                print(f"[{now()} JST] VERIFIED {ok}/{len(cubes)}", flush=True)
    except KeyboardInterrupt:
        for p in ps: p.kill()
        print("\n[interrupted] verified cubes are kept; run again to resume"); return
    ok = len(verified_ids(a.outdir))
    line = f"[{now()} JST] n={a.n} depth={a.depth}: VERIFIED {ok}/{len(cubes)} cubes (cadical DRAT proofs checked by drat-trim); all={'YES' if ok == len(cubes) else 'no'}"
    print(line)
    with open(os.path.join(a.outdir, "FINAL.txt"), "a", encoding="utf-8") as f: f.write(line + "\n")


if __name__ == "__main__":
    main()
