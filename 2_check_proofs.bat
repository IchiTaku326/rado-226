@echo off
rem Step 2 (proof check): every cube gets a CaDiCaL DRAT proof that drat-trim must accept.
rem Needs WSL with python3, and the binaries bin_linux/cadical and bin_linux/drat-trim (see bin_linux/README.md).
rem Resumable: run again to continue.
cd /d %~dp0
wsl -e bash -c "cd \"$(wslpath '%~dp0')\" && python3 tools/verify_proofs.py --workers 11 --outdir results/proof_check_n226"
type results\proof_check_n226\FINAL.txt
pause
