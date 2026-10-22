@echo off
rem Build the paper: needs a LaTeX installation (MiKTeX or TeX Live) with latexmk.
rem No LaTeX? Upload paper\main.tex to https://www.overleaf.com and compile there.
cd /d %~dp0paper
latexmk -pdf -interaction=nonstopmode main.tex
pause
