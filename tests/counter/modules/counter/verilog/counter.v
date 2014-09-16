//-----------------------------------------------------
// Design      : Simple 8-bit verilog counter
// Author      : Javier D. Garcia-Lasheras
//-----------------------------------------------------

module counter  (
    clock,
    clear,
    count,
    Q
);

//--------- Output Ports ------------------------------
    output [7:0] Q;

//--------- Input Ports -------------------------------
    input clock, clear, count;

//--------- Internal Variables ------------------------
    reg [7:0] Q;

//--------- Code Starts Here --------------------------
always @(posedge clock)
if (clear) begin
    Q <= 8'b0 ;
end else if (count) begin
    Q <= Q + 1;
end

endmodule 
