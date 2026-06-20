#!/usr/bin/env bash
# Render startup script
cd "$(dirname "$0")" || exit 1
exec python -m src.cli exemplos/site/site.spt
