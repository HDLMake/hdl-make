#!/bin/bash

hdlmake quartus-project

# Quartus bin needs to be exported to path
quartus_sh --tcl_eval load_package flow \; project_open myfilter \; execute_flow -compile

