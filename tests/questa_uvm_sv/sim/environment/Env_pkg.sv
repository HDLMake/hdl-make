//                              -*- Mode: Verilog -*-
// Filename        : Env_pkg.sv
// Description     : Package containing environment's components.
// Author          : Adrian Fiergolski
// Created On      : Thu Sep 18 10:48:26 2014
// Last Modified By: Adrian Fiergolski
// Last Modified On: Thu Sep 18 10:48:26 2014
// Update Count    : 0
// Status          : Unknown, Use with caution!

`ifndef ENG_PKG_SV
 `define ENG_PKG_SV

`include <mvc_macros.svh>
`include <mvc_pkg.sv>

package Env_pkg;
   import uvm_pkg::*;
`include <uvm_macros.svh>

`include "env.sv"
   
endpackage // Env_pkg
   
`endif
