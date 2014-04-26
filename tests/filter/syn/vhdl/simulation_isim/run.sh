#!/bin/bash

hdlmake 

make && make fuse TOP_MODULE=tb_myfilter && ./isim_proj -tclbatch isim_cmd 

