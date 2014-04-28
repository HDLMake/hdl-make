#!/bin/bash

hdlmake 

make && make fuse TOP_MODULE=half2_tb && ./isim_proj -tclbatch isim_cmd 

