#!/usr/bin/env bash

SCRIPT_DIR=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)
ZELLIG_CONFIG="-l ${SCRIPT_DIR}/layout.kdl"

zellij ${ZELLIG_CONFIG} || bash <(curl -L zellij.dev/launch) ${ZELLIG_CONFIG}
