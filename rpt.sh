#!/bin/sh
set -eu

rm ./tests/ships/generated_md/*

uv run pytest

cd ./tests/ships/generated_md/
for f in *.md; do pandoc "$f" -o "${f%.md}.html"; done
for f in *.md; do pandoc "$f" -o "${f%.md}.pdf"; done
