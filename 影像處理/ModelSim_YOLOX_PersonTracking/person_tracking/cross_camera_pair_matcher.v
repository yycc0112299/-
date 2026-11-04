`timescale 1ns/1ps
// Fixed-point, single-pair cross-camera confirmation for the existing
// 24-bit ROI feature format: {top_color, bottom_color, top_percent, bottom_percent}.
// The external scheduler must present one already-selected A/B person pair per frame.
module cross_camera_pair_matcher #(
 parameter [7:0] MAX_PERCENT_DELTA = 8'd35,
 parameter [1:0] REQUIRED_HITS = 2'd3
)(
 input wire clk,
 input wire reset,
 input wire observation_valid,
 input wire pair_present,
 input wire a_valid,
 input wire b_valid,
 input wire [23:0] feature_a,
 input wire [23:0] feature_b,
 output wire feature_similar,
 output reg candidate_valid,
 output reg confirmed,
 output reg [1:0] consecutive_hits
);
 function [7:0] absolute_difference;
  input [7:0] first;
  input [7:0] second;
  begin
   if (first >= second) absolute_difference = first - second;
   else absolute_difference = second - first;
  end
 endfunction

 // Color code zero (black) is valid. Validity is carried separately so that a
 // black-clothing feature cannot be mistaken for an invalid feature.
 assign feature_similar = a_valid && b_valid
     && feature_a[23:16] == feature_b[23:16]
     && absolute_difference(feature_a[15:8], feature_b[15:8]) <= MAX_PERCENT_DELTA
     && absolute_difference(feature_a[7:0], feature_b[7:0]) <= MAX_PERCENT_DELTA;

 always @(posedge clk) begin
  if (reset) begin
   candidate_valid <= 1'b0;
   confirmed <= 1'b0;
   consecutive_hits <= 2'd0;
  end else begin
   candidate_valid <= 1'b0;
   confirmed <= 1'b0;
   // Only a completed A/B frame-pair is an observation. Idle pixel clocks
   // between frames preserve history; an observed missing or dissimilar pair
   // deliberately breaks continuity.
   if (observation_valid) begin
    if (!pair_present || !feature_similar) begin
     consecutive_hits <= 2'd0;
    end else begin
     candidate_valid <= 1'b1;
     if (consecutive_hits >= REQUIRED_HITS - 1'b1) begin
      consecutive_hits <= REQUIRED_HITS;
      confirmed <= 1'b1;
     end else begin
      consecutive_hits <= consecutive_hits + 1'b1;
     end
    end
   end
  end
 end
endmodule
