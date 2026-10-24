#!/bin/sh
# Mantener Python del proyecto y obtener las herramientas EDA del flake fijado.
set -eu
project_root=$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)
openlane_root=${OPENLANE_ROOT:-"$HOME/openlane2"}
mkdir -p "$project_root/build/cache"
export XDG_CACHE_HOME=${XDG_CACHE_HOME:-"$project_root/build/cache"}
exec nix develop "path:$project_root/scripts/ppa/openlane" \
    --override-input openlane "path:$openlane_root" --no-write-lock-file --accept-flake-config \
    --max-jobs 2 --cores 2 \
    -c "${PPA_PYTHON:-/usr/bin/python3}" "$project_root/scripts/ppa.py" physical \
    --openlane-root "$openlane_root" "$@"
