#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
python3 src/prepare_universe.py
python3 src/imds_engine.py
