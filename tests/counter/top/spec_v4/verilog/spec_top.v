//---------------------------------------------------------------------
// Design  : Counter verilog top module, SPEC (Simple PCIe Carrier)
// Author  : Javier D. Garcia-Lasheras
//---------------------------------------------------------------------

module spec_top (
    clear_i,
    count_i,
    clock_i,
    led_o
);

input clear_i, count_i, clock_i;
output [3:0] led_o;

wire s_clock, s_clear, s_count; 
wire [7:0] s_Q;

counter u1(
    .clock(s_clock),
    .clear(s_clear),
    .count(s_count),
    .Q(s_Q)
);

assign s_clock = clock_i;
assign s_clear = ~clear_i;
assign s_count = ~count_i;
assign led_o[3:0] = ~s_Q[7:4];

endmodule
