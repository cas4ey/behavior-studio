#!/bin/sh
SCRIPT_DIR=`dirname "$0"`
python $SCRIPT_DIR/source/main.py -c $SCRIPT_DIR/config/config.xml $@
