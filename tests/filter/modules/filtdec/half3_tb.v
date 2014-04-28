`timescale 1ns / 1ns

// sine-based testing of pass band on channel b is quite stringent:
// reference sine wave has no phase shift (execpt for compensation of
// the pipeline delay), and a small amplitude change (predicatble from
// theory for the non-DC input).  Only +/-1 bit error is allowed, with
// almost no bias.  rms error should in principle be 1/sqrt(12) = 0.29,
// we demand it be less than 0.33.

module half3_tb;

reg clk;
reg tracex=0,tracea=0,traceb=0;
reg peak_fail=0, avg_fail=0, rms_fail=0, fail=0;
integer cc, nsamp=0, offbyone=0, sum=0;
initial begin
	if ($test$plusargs("vcd")) begin
		$dumpfile("half3.vcd");
		$dumpvars(5,half3_tb);
	end
	if ($test$plusargs("tracex")) tracex=1;
	if ($test$plusargs("tracea")) tracea=1;
	if ($test$plusargs("traceb")) traceb=1;
	for (cc=0; cc<140; cc=cc+1) begin
		clk=0; #5;
		clk=1; #5;
	end
	rms_fail = offbyone > (nsamp+2)/3;
	avg_fail = (sum > 4) || (sum < -4);
	fail = peak_fail | avg_fail | rms_fail;
	$display("x %d %d %d %d %s",nsamp,offbyone,sum,peak_fail,fail?"FAIL":"PASS");
	$finish();
end

reg signed [15:0] ina=0, inb=0, sine=0;
reg signed [16:0] sineref=0;
reg ing=0;
integer noise;
integer nseed=1234;

reg [1:0] abc=0;
wire ab=abc[1];
wire cs=abc[0];  // cos vs. sin on a and b inputs
always @(posedge clk) begin
	abc <= abc+1;
	sine    = $floor(30000.0*$sin((cc   )*0.0798)+0.5);
	sineref = $floor(59992.8*$sin((cc-10)*0.0798)+0.5);
	ina <= (cc==4 || cc==17 || cc==30 || cc==43) ? 1024 : 0;
	//inb <= (cc>30) ? 28000 : -28000;
	inb <= cs ? sine : 0;
end

wire signed [16:0] outd;
half3 dut(.clk(clk), .a(ina), .b(inb), .ab(ab), .d(outd));

reg fault;
always @(negedge clk) begin
	fault=0;
	if ((abc==0) && (cc>16)) begin
		nsamp = nsamp+1;
		sum = sum + outd - sineref;
		if (outd!=sineref) offbyone=offbyone+1;
		fault = (outd>sineref+1) || (outd<sineref-1);
		if (fault) peak_fail=1;
	end
	if (tracex | (tracea & (ab==0)) | (traceb & (abc==0)))
		 $display("%d %d %d %d %d %d", abc, ina, inb, outd, sineref, outd-sineref);
end
endmodule
