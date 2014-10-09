//                              -*- Mode: Verilog -*-
// Filename        : sequence.sv
// Description     : An example sequence item.
// Author          : Adrian Fiergolski
// Created On      : Thu Sep 18 10:47:00 2014
// Last Modified By: Adrian Fiergolski
// Last Modified On: Thu Sep 18 10:47:00 2014
// Update Count    : 0
// Status          : Unknown, Use with caution!

class sequenceA extends uvm_sequence_item;
   
   `uvm_object_utils_begin(sequenceA)
   `uvm_object_utils_end
   
   //Function: new
   //Creates a new <sequenceA> with the given ~name~..
   function new(string name="");
      super.new(name);
   endfunction // new

endclass // sequenceA
