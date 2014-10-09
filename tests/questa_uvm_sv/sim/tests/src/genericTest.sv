//                              -*- Mode: Verilog -*-
// Filename        : genericTest.sv
// Description     : The generic test
// Author          : Adrian Fiergolski
// Created On      : Thu Sep 18 10:34:01 2014
// Last Modified By: Adrian Fiergolski
// Last Modified On: Thu Sep 18 10:34:01 2014
// Update Count    : 0
// Status          : Unknown, Use with caution!

timeunit 1ns;
timeprecision 1ps;

import uvm_pkg::*;
`include <uvm_macros.svh>

`include "Env_pkg.sv"
`include "FullTest_pkg.sv"

`include "top.sv"

import Env_pkg::*;
import FullTest_pkg::*;

//Class: genericTest
class genericTest extends uvm_test;

   env i_env;
   
   `uvm_component_utils_begin(genericTest)
   `uvm_component_utils_end

   //Function: new
   //Creates a new <genericTest> with the given ~name~ and ~parent~.
   function new(string name="", uvm_component parent);
      super.new(name, parent);
   endfunction // new

   function void build_phase(uvm_phase phase);
      super.build_phase(phase);
      i_env = env::type_id::create("env", this);
   endfunction

endclass // genericTest
