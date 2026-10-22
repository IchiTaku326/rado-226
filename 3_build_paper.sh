#!/usr/bin/env bash
# Build the paper (needs LaTeX with latexmk), or upload paper/main.tex to Overleaf.
cd "$(dirname "$0")/paper" && latexmk -pdf -interaction=nonstopmode main.tex
