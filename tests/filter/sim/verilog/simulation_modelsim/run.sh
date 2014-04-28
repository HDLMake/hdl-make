#!/bin/bash

hdlmake

make 
vsim -c -do vsim.do half2_tb 


