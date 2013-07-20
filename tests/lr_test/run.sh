#!/bin/bash

# Tests for empty parameter
if [ -z $1 ] ; then
	echo "You must specify a top module testbench!";
	echo "Usage: $0 <TOP_MODULE_WITHOUT_EXTENSION>";
	exit 1;
fi

make && make fuse TOP_MODULE=$1 && ./isim_proj -view wave.wcfg -tclbatch isim_cmd -gui
