#!/usr/bin/env bash

# Script to populate deployment with absolute paths of environment

if [[ "$1" == "-h" || "$1" == "--help" || "$#" -ne 2 ]]; then
    echo "Usage: $0 <path-to-odin-data-prefix> <path-to-venv>"
    exit 0
fi

ODIN_DATA=$1
VENV=$2

SCRIPT_DIR=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)

mkdir ${SCRIPT_DIR}/local
cp ${SCRIPT_DIR}/templates/* ${SCRIPT_DIR}/local

SERVER="${SCRIPT_DIR}/local/stOdinServer.sh"
FR="${SCRIPT_DIR}/local/stFrameReceiver1.sh"
FR_CONFIG="${SCRIPT_DIR}/local/fr1.json"
FP="${SCRIPT_DIR}/local/stFrameProcessor1.sh"
FP_CONFIG="${SCRIPT_DIR}/local/fp1.json"
META="${SCRIPT_DIR}/local/stMetaWriter.sh"
LAYOUT="${SCRIPT_DIR}/local/layout.kdl"

sed -i "s+<ODIN_DATA>+${ODIN_DATA}+g" ${FR} ${FR_CONFIG} ${FP} ${FP_CONFIG}
sed -i "s+<VENV>+${VENV}+g" ${SERVER} ${META}
sed -i "s+<SCRIPT_DIR>+${SCRIPT_DIR}/local+g" ${LAYOUT}
