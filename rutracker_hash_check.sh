#!/usr/bin/env bash
set -euo pipefail

LINKS_FILE="/home/clawd/.openclaw/workspace/data/rutracker_links.txt"
HASH_FILE="/home/clawd/.openclaw/workspace/data/rutracker_hash.txt"
SCRIPT="/home/clawd/.openclaw/workspace/data/rutracker_hash_check.py"

python3 "$SCRIPT" --links-file "$LINKS_FILE" --hash-file "$HASH_FILE"
