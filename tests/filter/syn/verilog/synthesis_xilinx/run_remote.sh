#!/bin/bash

echo "set the appropriated HDLMAKE_RSYNTH variables in this file"

export HDLMAKE_RSYNTH_USER=javi
export HDLMAKE_RSYNTH_ISE_PATH="/opt/Xilinx/14.7/ISE_DS/ISE/bin/lin/"
export HDLMAKE_RSYNTH_SERVER="192.168.0.17"

hdlmake
make remote
make sync
make cleanremote

