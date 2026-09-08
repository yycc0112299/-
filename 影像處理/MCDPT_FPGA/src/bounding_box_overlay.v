`include "mcdpt_defs.vh"
module bounding_box_overlay(input [9:0] x,y,input [7:0] box_x,input [6:0] box_y,input enable,output hit);
 wire [7:0] sx=x>>2;wire [6:0] sy=y>>2;
 assign hit=enable&&(sx>=box_x)&&(sx<box_x+`BOX_W)&&(sy>=box_y)&&(sy<box_y+`BOX_H)&&
  ((sx==box_x)||(sx==box_x+`BOX_W-1)||(sy==box_y)||(sy==box_y+`BOX_H-1));
endmodule
