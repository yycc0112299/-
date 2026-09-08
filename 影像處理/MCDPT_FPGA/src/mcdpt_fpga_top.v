`include "mcdpt_defs.vh"
module mcdpt_fpga_top(input clk100,reset,btn_start,output reg [3:0] vga_r,vga_g,vga_b,output vga_hsync,vga_vsync);
 reg start_q,auto_start;wire [7:0] tx;wire [6:0] ty;wire done;wire [1:0] status;wire [14:0] ta,tb;
 wire [14:0] da;wire [3:0] pa_t,pb_t,pa_d,pb_d;wire [3:0] pix;wire [9:0] vx,vy;wire active,ce,hit;
 wire [3:0] sr,sg,sb;wire [7:0] boxx=(status==0)?`REF_X:tx;wire [6:0] boxy=(status==0)?`REF_Y:ty;
 always @(posedge clk100)begin start_q<=btn_start;if(reset)auto_start<=1;else if(auto_start)auto_start<=0;end
 tracker_fsm tracker(clk100,reset,auto_start|(btn_start&~start_q),ta,tb,pa_t,pb_t,tx,ty,done,status);
 vga_timing timing(clk100,reset,vx,vy,active,vga_hsync,vga_vsync,ce);
 assign da=active?((vy>>2)*`FRAME_W+(vx>>2)):0;
 frame_rom_a rom_a(clk100,ta,da,pa_t,pa_d);frame_rom_b rom_b(clk100,tb,da,pb_t,pb_d);
 assign pix=(status==0)?pa_d:pb_d;
 bounding_box_overlay overlay(vx,vy,boxx,boxy,1'b1,hit);status_display colors(status,sr,sg,sb);
 always @* begin vga_r=0;vga_g=0;vga_b=0;if(active)begin if(hit)begin vga_r=sr;vga_g=sg;vga_b=sb;end else begin vga_r=pix;vga_g=pix;vga_b=pix;end end end
endmodule
