`timescale 1ns/1ps
module tb_axis_dual_rgb_stream_adapter;
 reg clk=0; always #5 clk=~clk;
 reg reset=1, valid=0, last=0; reg [63:0] data=0;
 wire ready,pixel_valid,frame_start,boundary_error; wire [23:0] a,b;
 integer checks=0;
 axis_dual_rgb_stream_adapter #(.FRAME_PIXELS(4)) dut(.clk(clk),.reset(reset),.s_axis_tdata(data),.s_axis_tvalid(valid),.s_axis_tready(ready),.s_axis_tlast(last),.pixel_valid(pixel_valid),.frame_start(frame_start),.pixel_rgb_a(a),.pixel_rgb_b(b),.frame_boundary_error(boundary_error));
 task check; input ok; input [255:0] label; begin if(ok!==1) $fatal(1,"FAIL %0s",label); checks=checks+1; end endtask
 task send; input [23:0] av; input [23:0] bv; input lv; input startv; begin
  @(negedge clk); data={8'd0,bv,8'd0,av}; valid=1; last=lv; #1; check(ready&&pixel_valid&&frame_start==startv&&a==av&&b==bv,"AXIS word mapped to both RGB lanes"); @(negedge clk); valid=0; last=0;
 end endtask
 initial begin
  repeat(2) @(posedge clk); reset=0;
  send(24'h112233,24'haabbcc,0,1); send(24'h010203,24'h040506,0,0); send(24'h070809,24'h0a0b0c,0,0); send(24'h0d0e0f,24'h101112,1,0);
  check(!boundary_error,"correct TLAST frame boundary");
  send(24'h111111,24'h222222,1,1); check(boundary_error,"early TLAST is reported");
  $display("AXIS_DUAL_RGB_STREAM_ADAPTER_PASS checks=%0d",checks); $finish;
 end
 initial begin #10000; $fatal(1,"timeout"); end
endmodule
