//                              -*- Mode: Verilog -*-
// Filename        : env.sv
// Description     : Example UVM environment
// Author          : Adrian Fiergolski
// Created On      : Thu Sep 18 11:04:56 2014
// Last Modified By: Adrian Fiergolski
// Last Modified On: Thu Sep 18 11:04:56 2014
// Update Count    : 0
// Status          : Unknown, Use with caution!

class env extends uvm_env;

   `uvm_component_utils_begin(env)
   `uvm_component_utils_end

   //Function: new
   //Creates a new <env> with the given ~name~ and ~parent~.
   function new(string name="", uvm_component parent);
      super.new(name, parent);
   endfunction // new


endclass // env
