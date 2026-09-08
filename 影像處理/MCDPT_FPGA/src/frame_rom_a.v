`include "mcdpt_defs.vh"
module frame_rom_a(input clk, input [14:0] addr_a, addr_b, output reg [3:0] data_a, data_b);
  (* rom_style = "block" *) reg [3:0] rom [0:`FRAME_W*`FRAME_H-1];
  integer i,x,y,lx,ly,bx,by,p;
  initial begin
    for (i=0;i<`FRAME_W*`FRAME_H;i=i+1) begin
      x=i%`FRAME_W; y=i/`FRAME_W; p=(x/16+y/12)%4;
      if (x>=`REF_X && x<`REF_X+`BOX_W && y>=`REF_Y && y<`REF_Y+`BOX_H) begin
        lx=x-`REF_X; ly=y-`REF_Y; bx=lx/8; by=ly/8;
        p=3+((bx*3+by*5+(lx/4)+(ly/4))%11);
      end
      rom[i]=p[3:0];
    end
  end
  always @(posedge clk) begin data_a<=rom[addr_a]; data_b<=rom[addr_b]; end
endmodule
