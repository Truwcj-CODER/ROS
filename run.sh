#!/bin/bash
source "$(dirname "$0")/.env"

if [ "$DEV_MODE" = "true" ]; then
    export ACTIVE_IMAGE=$DEV_IMAGE
    export ACTIVE_VOLUME=$DEV_VOLUME
    export ACTIVE_RUNTIME=$DEV_RUNTIME
    echo "[MODE] DEV - laptop"
else
    export ACTIVE_IMAGE=$JETSON_IMAGE
    export ACTIVE_VOLUME=$JETSON_VOLUME
    export ACTIVE_RUNTIME=$JETSON_RUNTIME
    echo "[MODE] PROD - Jetson"
fi

docker compose up -d "$@"
