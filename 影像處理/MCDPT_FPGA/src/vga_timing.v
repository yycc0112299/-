module vga_timing(input clk,rst,output [9:0] x,y,output active,hsync,vsync,pixel_ce);
 reg [1:0] div;reg [9:0] h,v;assign x=h;assign y=v;assign pixel_ce=(div==0);
 assign active=(h<640)&&(v<480);assign hsync=!((h>=656)&&(h<752));assign vsync=!((v>=490)&&(v<492));
 always @(posedge clk)begin if(rst)begin div<=0;h<=0;v<=0;end else begin div<=div+1'b1;if(div==0)begin if(h==799)begin h<=0;if(v==524)v<=0;else v<=v+1'b1;end else h<=h+1'b1;end end end
endmodule
