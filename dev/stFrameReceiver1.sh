#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"

/scratch/development/odin/odin-data/vscode_prefix//bin/frameReceiver --io-threads 2 --ctrl=tcp://0.0.0.0:10000 --config=$SCRIPT_DIR/fr1.json --log-config $SCRIPT_DIR/log4cxx.xml
