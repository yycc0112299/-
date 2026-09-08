module frame_selector(input select_b, input [3:0] pixel_a,pixel_b, output [3:0] pixel_out);
  assign pixel_out=select_b?pixel_b:pixel_a;
endmodule
