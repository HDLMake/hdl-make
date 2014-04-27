#!/bin/bash

hdlmake

make 
vsim -c -do vsim.do tb_myfilter 


