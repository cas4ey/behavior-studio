#!/bin/sh
BEHAVIOR_STUDIO_ROOT=`dirname "$0"`
python $BEHAVIOR_STUDIO_ROOT/source/main.py -c $BEHAVIOR_STUDIO_ROOT/config/config.xml $@
