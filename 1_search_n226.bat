@echo off
rem Step 1 (upper bound): cube-and-conquer search for n=226 with 11 workers. Resumable: run again to continue.
rem Needs: python 3 and  pip install python-sat
cd /d %~dp0
:loop
python tools\cube_search.py --a 2 --b 3 --k 4 --n 226 --depth 10 --workers 11 --backend pysat --budget 20000 --outdir results\cube_search_n226
if exist results\cube_search_n226\FINAL.txt goto end
if exist results\cube_search_n226\cert_*.json goto end
echo [restart in 30 s]
timeout /t 30 /nobreak >nul
goto loop
:end
type results\cube_search_n226\FINAL.txt
pause
