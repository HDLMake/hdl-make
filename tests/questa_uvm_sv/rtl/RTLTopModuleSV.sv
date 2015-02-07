//                              -*- Mode: Verilog -*-
// Filename        : RTLTopModuleSV.sv
// Description     : RTL top module (DUT).
// Author          : Adrian Fiergolski
// Created On      : Thu Sep 18 10:50:28 2014
// Last Modified By: Adrian Fiergolski
// Last Modified On: Thu Sep 18 10:50:28 2014
// Update Count    : 0
// Status          : Unknown, Use with caution!

module RTLTopModuleSV;

   logic l1a;
   initial
     l1a <= RTL_SVPackage::CONST;
   
   includeModuleSV incl();
   ipcore ip();

endmodule // RTLTopModuleSV
