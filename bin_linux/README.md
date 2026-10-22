# bin_linux

`tools/verify_proofs.py` (run inside Linux or WSL) looks for two executables here:

- `cadical` – SAT solver that writes DRAT proofs (https://github.com/arminbiere/cadical, MIT licence)
- `drat-trim` – DRAT proof checker (https://github.com/marijnheule/drat-trim, MIT licence)

The binaries are **not** stored in this repository. Build them inside WSL/Linux:

```
git clone https://github.com/arminbiere/cadical && cd cadical && ./configure && make -j4 && cp build/cadical ../bin_linux/ && cd ..
git clone https://github.com/marijnheule/drat-trim && cd drat-trim && make && cp drat-trim ../bin_linux/ && cd ..
```

Versions used for the recorded run: not recorded precisely (built from the default branch around 2026-10-20/21 JST).
Please note the commit hashes you use when you re-run the check.
