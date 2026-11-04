`timescale 1ns/1ps
// Converts one 64-bit AXI4-Stream word into two lock-step RGB888 pixels.
// Layout: bits [23:0] = camera A RGB, [55:32] = camera B RGB.  One DMA
// transfer must contain exactly FRAME_PIXELS words; TLAST is checked at the
// final word and a bad boundary is reported without stalling the video path.
module axis_dual_rgb_stream_adapter #(
 parameter [31:0] FRAME_PIXELS = 32'd307200
)(
 input wire clk, input wire reset,
 input wire [63:0] s_axis_tdata, input wire s_axis_tvalid, output wire s_axis_tready,
 input wire s_axis_tlast,
 output wire pixel_valid, output wire frame_start,
 output wire [23:0] pixel_rgb_a, output wire [23:0] pixel_rgb_b,
 output reg frame_boundary_error
);
 reg [31:0] pixel_index;
 assign s_axis_tready = 1'b1;
 assign pixel_valid = s_axis_tvalid;
 assign frame_start = s_axis_tvalid && pixel_index == 0;
 assign pixel_rgb_a = s_axis_tdata[23:0];
 assign pixel_rgb_b = s_axis_tdata[55:32];

 always @(posedge clk) begin
  if (reset) begin
   pixel_index <= 0;
   frame_boundary_error <= 0;
  end else if (s_axis_tvalid) begin
   if ((pixel_index == FRAME_PIXELS - 1) != s_axis_tlast)
    frame_boundary_error <= 1'b1;
   if (pixel_index == FRAME_PIXELS - 1)
    pixel_index <= 0;
   else
    pixel_index <= pixel_index + 1'b1;
  end
 end
endmodule
