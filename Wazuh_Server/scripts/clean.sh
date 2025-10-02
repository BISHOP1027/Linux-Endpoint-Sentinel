#!/usr/bin/env bash
set -euo pipefail
echo "[+] Cleaning unused containers, networks, volumes"
docker container prune -f
docker network prune -f
docker volume prune -f

