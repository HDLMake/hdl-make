// Combined half-band filter and decimator
// See concept1.eps for general DSP idea
// See actual2.eps for graphical DSP representation
// Half-band filter configuration is
//   -1 + 9 z^{-2} + 16 z^{-3} + 9 z^{-4} - 1 z^{-6}

// Decimation is controlled by the ab input, which _must_
// be clk/2.  Output d gives a results when ab is low, and
// b results when ab is high.  b results are delayed one
// cycle, corresponding to something like simultaneous
// sampling at the input.

// See actual2.eps
// Total 5 cycle latency for a, 6 cycles for b.
// Uses about 172 Slice Flip Flops and 174 4LUTs in Spartan-3.

// Larry Doolittle, LBNL, Oct. 2012

`timescale 1ns / 1ns

module half2(
	input clk,  // timespec 5.2 ns
	input signed [15:0] a,
	input signed [15:0] b,
	input ab,
	output signed [16:0] d
);

// buffer B one cycle, provides "simultaneous sampling"
reg [15:0] bb=0;  always @(posedge clk) bb <= b;

// input switch
// left and right take their names from actual2.eps
wire signed [15:0] left  = ab ? a : bb;
wire signed [15:0] right = ab ? bb : a;

wire signed [15:0] dl1;
reg_delay #(.dw(16), .len(3)) l1(.clk(clk),.gate(1'b1),.din(left),.dout(dl1));

wire signed [15:0] dr1, dr2;
reg_delay #(.dw(16), .len(2)) r1(.clk(clk),.gate(1'b1),.din(right),.dout(dr1));
reg_delay #(.dw(16), .len(4)) r2(.clk(clk),.gate(1'b1),.din(dr1),  .dout(dr2));

`define SAT(x,old,new) ((~|x[old:new] | &x[old:new]) ? x : {x[old],{new{~x[old]}}})

reg signed [16:0] s1=0, s2=0;
reg signed [20:0] m9=0;
reg signed [21:0] s3=0, s4=0;
always @(posedge clk) begin
	s1 <= right + dr1;
	s2 <= right + dr2;
	m9 <= s1 + (s1<<<3);
	s3 <= m9 + (dl1<<<4) + 8;  // un-bias the truncation step
	s4 <= s3 - s2;
end
wire signed [17:0] penult = s4[21:4];  // truncate 4 lsb
assign d = `SAT(penult,17,16);  // clip 1 msb

endmodule
