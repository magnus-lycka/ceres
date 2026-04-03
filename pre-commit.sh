#!/bin/sh
set -eu

uvx ruff check --no-fix src
