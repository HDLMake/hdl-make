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

//--------- Cycles per second -------------------------
    parameter cycles_per_second = 12000000;

//--------- Output Ports ------------------------------
    output [7:0] Q;

//--------- Input Ports -------------------------------
    input clock, clear, count;

//--------- Internal Variables ------------------------
    reg ready = 0;
    reg [23:0] divider;
    reg [7:0] Q;

//--------- Code Starts Here --------------------------

    always @(posedge clock) begin
       if (ready)
         begin
            if (divider == cycles_per_second)
              begin
                 divider <= 0;
                 Q <= {Q[6:0], Q[7]};
              end
            else
              divider <= divider + 1;
         end
       else
         begin
            ready <= 1;
            Q <= 8'b00010001;
            divider <= 0;
         end
    end


endmodule 
