`timescale 1ns / 1ns

module reg_delay(clk, gate, din, dout);
parameter dw=16;
parameter len=4;
	input clk;
	input gate;
	input [dw-1:0] din;
	output [dw-1:0] dout;

// len clocks of delay.  Xilinx should turn this into
//   dw*floor((len+15)/16)
// SRL16 shift registers, since there are no resets.
generate if (len > 1) begin: usual
	reg [dw*len-1:0] shifter=0;
	always @(posedge clk) if (gate) shifter <= {shifter[dw*len-1-dw:0],din};
	assign dout = shifter[dw*len-1:dw*len-dw];
end else if (len > 0) begin: degen1
	reg [dw*len-1:0] shifter=0;
	always @(posedge clk) if (gate) shifter <= din;
	assign dout = shifter[dw*len-1:dw*len-dw];
end else begin: degen0
        assign dout = din;
end
endgenerate

endmodule
