#!/usr/bin/env bash

# Script to populate deployment with absolute paths of environment

if [[ "$1" == "-h" || "$1" == "--help" || "$#" -ne 2 ]]; then
    echo "Usage: $0 <path-to-odin-data-prefix> <path-to-venv>"
    exit 0
fi

ODIN_DATA=$1
VENV=$2

SCRIPT_DIR=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)
SERVER="${SCRIPT_DIR}/stOdinServer.sh"
FR="${SCRIPT_DIR}/stFrameReceiver1.sh"
FR_CONFIG="${SCRIPT_DIR}/fr1.json"
FP="${SCRIPT_DIR}/stFrameProcessor1.sh"
FP_CONFIG="${SCRIPT_DIR}/fp1.json"
META="${SCRIPT_DIR}/stMetaWriter.sh"
LAYOUT="${SCRIPT_DIR}/layout.kdl"

sed -i "s+<ODIN_DATA>+${ODIN_DATA}+g" ${FR} ${FR_CONFIG} ${FP} ${FP_CONFIG}
sed -i "s+<VENV>+${VENV}+g" ${SERVER} ${META}
sed -i "s+<SCRIPT_DIR>+${SCRIPT_DIR}+g" ${LAYOUT}
