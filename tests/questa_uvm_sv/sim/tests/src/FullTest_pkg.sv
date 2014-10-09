//                              -*- Mode: Verilog -*-
// Filename        : FullTest_pkg.sv
// Description     : The package contains custom sequences
// Author          : Adrian Fiergolski
// Created On      : Thu Sep 18 10:35:56 2014
// Last Modified By: Adrian Fiergolski
// Last Modified On: Thu Sep 18 10:35:56 2014
// Update Count    : 0
// Status          : Unknown, Use with caution!

`ifndef FULLTEST_PKG_SV
 `define FULLTEST_PKG_SV

//Title: FullTest_pkg

//Package: FullTest_pkg
//The package contains sequences available for full tests.
package FullTest_pkg;

   import uvm_pkg::*;
 `include <uvm_macros.svh>

 `include "sequence.sv"
   
endpackage // FullTest_pkg

`endif
