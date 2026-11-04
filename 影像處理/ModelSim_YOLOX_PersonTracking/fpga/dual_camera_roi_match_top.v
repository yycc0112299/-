`timescale 1ns/1ps
// Synchronous two-camera ROI feature path.  YOLOX/CPU supplies one bbox for
// each camera frame; this module owns only RGB ROI feature extraction and the
// three-frame A/B confirmation rule.
module dual_camera_roi_match_top(
 input wire clk,
 input wire reset,
 input wire pixel_valid,
 input wire frame_start,
 input wire person_detected_a,
 input wire person_detected_b,
 input wire [23:0] pixel_rgb_a,
 input wire [23:0] pixel_rgb_b,
 input wire [9:0] x0_a, y0_a, x1_a, y1_a,
 input wire [9:0] x0_b, y0_b, x1_b, y1_b,
 output wire feature_valid_a,
 output wire feature_valid_b,
 output wire person_valid_a,
 output wire person_valid_b,
 output wire [23:0] feature_a,
 output wire [23:0] feature_b,
 output wire feature_similar,
 output wire candidate_valid,
 output wire confirmed,
 output wire [1:0] consecutive_hits
);
 wire [31:0] top_pixels_a, bottom_pixels_a, pixel_count_a;
 wire [31:0] top_pixels_b, bottom_pixels_b, pixel_count_b;
 reg observation_pending, pair_present_pending;
 reg [23:0] buffered_feature_a, buffered_feature_b;

 person_roi_stream roi_a(
  clk, reset, pixel_valid, frame_start, person_detected_a, pixel_rgb_a,
  x0_a, y0_a, x1_a, y1_a, feature_valid_a, person_valid_a, feature_a,
  top_pixels_a, bottom_pixels_a, pixel_count_a);
 person_roi_stream roi_b(
  clk, reset, pixel_valid, frame_start, person_detected_b, pixel_rgb_b,
  x0_b, y0_b, x1_b, y1_b, feature_valid_b, person_valid_b, feature_b,
  top_pixels_b, bottom_pixels_b, pixel_count_b);

 // ROI outputs are registered on the final pixel. Buffer them, then present a
 // single observation to the matcher on the next clock; long pixel gaps do not
 // erase the three-frame history.
 always @(posedge clk) begin
  if (reset) begin
   observation_pending <= 1'b0;
   pair_present_pending <= 1'b0;
   buffered_feature_a <= 24'd0;
   buffered_feature_b <= 24'd0;
  end else begin
   observation_pending <= feature_valid_a && feature_valid_b;
   if (feature_valid_a && feature_valid_b) begin
    pair_present_pending <= person_valid_a && person_valid_b;
    buffered_feature_a <= feature_a;
    buffered_feature_b <= feature_b;
   end
  end
 end

 cross_camera_pair_matcher matcher(
  .clk(clk), .reset(reset), .observation_valid(observation_pending),
  .pair_present(pair_present_pending), .a_valid(pair_present_pending),
  .b_valid(pair_present_pending), .feature_a(buffered_feature_a),
  .feature_b(buffered_feature_b), .feature_similar(feature_similar),
  .candidate_valid(candidate_valid), .confirmed(confirmed),
  .consecutive_hits(consecutive_hits));
endmodule
