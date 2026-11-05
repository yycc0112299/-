`timescale 1ns/1ps
module tb_yolox_command_path;
 reg clk=0; always #5 clk=~clk;
 reg reset=1, aresetn=0, frame_start=0; reg [31:0] stream_frame_id=0;
 reg [5:0] awaddr=0; reg awvalid=0; wire awready;
 reg [31:0] wdata=0; reg [3:0] wstrb=4'hf; reg wvalid=0; wire wready;
 wire [1:0] bresp; wire bvalid; reg bready=1;
 reg [5:0] araddr=0; reg arvalid=0; wire arready; wire [31:0] rdata; wire [1:0] rresp; wire rvalid; reg rready=1;
 reg result_event=0,confirmed_event=0,missing_event=0; wire cmd_valid,cmd_pair_present,cmd_accept,overrun,missing,irq; wire [31:0] cmd_frame_id;
 wire [9:0] ax0,ay0,ax1,ay1,bx0,by0,bx1,by1; wire pa,pb; wire [9:0] lax0,lay0,lax1,lay1,lbx0,lby0,lbx1,lby1;
 integer checks=0;
 yolox_bbox_axilite dut(.s_axi_aclk(clk),.s_axi_aresetn(aresetn),.s_axi_awaddr(awaddr),.s_axi_awvalid(awvalid),.s_axi_awready(awready),.s_axi_wdata(wdata),.s_axi_wstrb(wstrb),.s_axi_wvalid(wvalid),.s_axi_wready(wready),.s_axi_bresp(bresp),.s_axi_bvalid(bvalid),.s_axi_bready(bready),.s_axi_araddr(araddr),.s_axi_arvalid(arvalid),.s_axi_arready(arready),.s_axi_rdata(rdata),.s_axi_rresp(rresp),.s_axi_rvalid(rvalid),.s_axi_rready(rready),.command_valid(cmd_valid),.command_pair_present(cmd_pair_present),.command_frame_id(cmd_frame_id),.a_x0(ax0),.a_y0(ay0),.a_x1(ax1),.a_y1(ay1),.b_x0(bx0),.b_y0(by0),.b_x1(bx1),.b_y1(by1),.command_accept(cmd_accept),.overrun(overrun),.result_event(result_event),.confirmed_event(confirmed_event),.missing_event(missing_event),.irq(irq));
 yolox_frame_command_adapter adapter(.clk(clk),.reset(reset),.frame_start(frame_start),.stream_frame_id(stream_frame_id),.command_valid(cmd_valid),.command_pair_present(cmd_pair_present),.command_frame_id(cmd_frame_id),.command_a_x0(ax0),.command_a_y0(ay0),.command_a_x1(ax1),.command_a_y1(ay1),.command_b_x0(bx0),.command_b_y0(by0),.command_b_x1(bx1),.command_b_y1(by1),.command_accept(cmd_accept),.frame_command_missing(missing),.person_detected_a(pa),.person_detected_b(pb),.a_x0(lax0),.a_y0(lay0),.a_x1(lax1),.a_y1(lay1),.b_x0(lbx0),.b_y0(lby0),.b_x1(lbx1),.b_y1(lby1));
 task check; input condition; input [255:0] label; begin if(condition!==1) $fatal(1,"FAIL %0s",label); checks=checks+1; end endtask
 task write_reg; input [5:0] address; input [31:0] value; begin
  @(negedge clk); awaddr=address; wdata=value; awvalid=1; wvalid=1;
  while(!(awready&&wready)) @(posedge clk);
  @(negedge clk); awvalid=0; wvalid=0;
  while(!bvalid) @(posedge clk); @(negedge clk);
 end endtask
 initial begin
  repeat(2) @(posedge clk); aresetn=1; reset=0;
  write_reg(6'h1c,32'h9); // Enable result and overrun interrupt sources.
  @(negedge clk); result_event=1; @(negedge clk); result_event=0; #1;
  check(irq,"result event raises enabled IRQ");
  write_reg(6'h18,32'h1); #1; check(!irq,"write-one-to-clear deasserts IRQ");
  write_reg(6'h04,32'd42); write_reg(6'h08,{6'd0,10'd320,6'd0,10'd10}); write_reg(6'h0c,{6'd0,10'd400,6'd0,10'd20});
  write_reg(6'h10,{6'd0,10'd310,6'd0,10'd11}); write_reg(6'h14,{6'd0,10'd401,6'd0,10'd21}); write_reg(6'h00,32'h3);
  check(cmd_valid&&cmd_pair_present&&cmd_frame_id==42,"committed YOLOX command visible");
  write_reg(6'h00,32'h3); #1; check(overrun&&irq,"second pending command raises overrun IRQ");
  write_reg(6'h18,32'h8); #1; check(!irq,"overrun IRQ clear works");
  @(negedge clk); stream_frame_id=41; frame_start=1; @(negedge clk); frame_start=0; #1;
  check(missing&&!pa&&!pb&&cmd_valid,"wrong frame does not consume command");
  @(negedge clk); stream_frame_id=42; frame_start=1; @(negedge clk); frame_start=0; #1;
  check(pa&&pb&&lax0==10&&lay0==20&&lax1==320&&lay1==400,"A bbox latched on matching frame");
  check(lbx0==11&&lby0==21&&lbx1==310&&lby1==401,"B bbox latched on matching frame");
  @(posedge clk); #1; check(!cmd_valid,"accepted command clears mailbox");
  $display("YOLOX_COMMAND_PATH_PASS checks=%0d",checks); $finish;
 end
 initial begin #100000; $fatal(1,"timeout"); end
endmodule
