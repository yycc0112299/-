`timescale 1ns/1ps
`include "mcdpt_defs.vh"
module mcdpt_fpga_tb;
 reg clk=0,rst=0,start=0;wire [14:0] aa,ab;wire [3:0] pa,pb,unused_a,unused_b;wire [7:0] x;wire [6:0] y;wire done;wire [1:0] status;
 always #5 clk=~clk;
 frame_rom_a ra(clk,aa,15'd0,pa,unused_a);frame_rom_b rb(clk,ab,15'd0,pb,unused_b);
 tracker_fsm dut(clk,rst,start,aa,ab,pa,pb,x,y,done,status);
 initial begin rst=1;#50;@(posedge clk);rst=0;start=1;@(posedge clk);start=0;
   wait(done);if(x<`TARGET_X-`SEARCH_STRIDE||x>`TARGET_X+`SEARCH_STRIDE)$fatal(1,"tracked_x incorrect");if(y<`TARGET_Y-`SEARCH_STRIDE||y>`TARGET_Y+`SEARCH_STRIDE)$fatal(1,"tracked_y incorrect");$display("RESULT tracked_x=%0d tracked_y=%0d expected_x=%0d expected_y=%0d",x,y,`TARGET_X,`TARGET_Y);$display("MCDPT FPGA TRACKING TEST PASSED");$finish;
 end
 initial begin #20000000;$fatal(1,"tracking timeout");end
endmodule
