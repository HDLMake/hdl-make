//---------------------------------------------------------------------
// Design  : Counter verilog top module, iCEstick (Lattice iCE40)
// Author  : Javier D. Garcia-Lasheras
//---------------------------------------------------------------------

module icestick_top (
    clock_i,
    led_o_0,
    led_o_1,
    led_o_2,
    led_o_3,
    led_o_4,
);

input clock_i;
output led_o_0, led_o_1, led_o_2, led_o_3, led_o_4;

wire s_clock, s_clear, s_count; 
wire [7:0] s_Q;

counter u1(
    .clock(s_clock),
    .clear(s_clear),
    .count(s_count),
    .Q(s_Q)
);

assign s_clock = clock_i;
assign s_clear = 0;
assign s_count = 1;
assign led_o_4 = s_Q[7];
assign led_o_3 = s_Q[6];
assign led_o_2 = s_Q[5];
assign led_o_1 = s_Q[4];
assign led_o_0 = s_Q[3];

endmodule
