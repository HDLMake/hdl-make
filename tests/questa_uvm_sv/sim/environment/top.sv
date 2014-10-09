//                              -*- Mode: Verilog -*-
// Filename        : top.sv
// Description     : Top simulation module.
// Author          : Adrian Fiergolski
// Created On      : Thu Sep 18 10:47:27 2014
// Last Modified By: Adrian Fiergolski
// Last Modified On: Thu Sep 18 10:47:27 2014
// Update Count    : 0
// Status          : Unknown, Use with caution!

module automatic top;
   timeunit 1ns;
   timeprecision 1ps;

   RTLTopModuleSV sv();
   RTLTopModuleVHDL vhdl();
   RTLTopModuleVerilogSimulationModel vsm();
   
   initial
     run_test("genericTest");
   
endmodule // top
