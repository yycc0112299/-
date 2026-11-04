`timescale 1ns/1ps
module tb_dual_camera_roi_match_top;
 reg clk = 0;
 always #5 clk = ~clk;
 reg reset = 1, pixel_valid = 0, frame_start = 0;
 reg person_detected_a = 0, person_detected_b = 0;
 reg [23:0] pixel_rgb_a = 0, pixel_rgb_b = 0;
 reg [9:0] x0_a = 0, y0_a = 0, x1_a = 0, y1_a = 0;
 reg [9:0] x0_b = 0, y0_b = 0, x1_b = 0, y1_b = 0;
 wire feature_valid_a, feature_valid_b, person_valid_a, person_valid_b;
 wire [23:0] feature_a, feature_b;
 wire feature_similar, candidate_valid, confirmed;
 wire [1:0] consecutive_hits;
 integer pixel, checks = 0;

 dual_camera_roi_match_top dut(
  clk, reset, pixel_valid, frame_start, person_detected_a, person_detected_b,
  pixel_rgb_a, pixel_rgb_b, x0_a, y0_a, x1_a, y1_a, x0_b, y0_b, x1_b, y1_b,
  feature_valid_a, feature_valid_b, person_valid_a, person_valid_b, feature_a,
  feature_b, feature_similar, candidate_valid, confirmed, consecutive_hits);

 task check;
  input condition;
  input [511:0] message;
  begin
   if (condition !== 1'b1) begin
    $display("FAIL: %0s hits=%0d candidate=%b confirmed=%b fa=%h fb=%h",
      message, consecutive_hits, candidate_valid, confirmed, feature_a, feature_b);
    $fatal(1, "dual top regression failed");
   end
   checks = checks + 1;
  end
 endtask

 task whole_frame;
  input [23:0] color_a;
  input [23:0] color_b;
  input [1:0] expected_hits;
  input expected_confirmed;
  begin
   @(negedge clk);
   person_detected_a = 1; person_detected_b = 1;
   x0_a = 0; y0_a = 0; x1_a = 640; y1_a = 480;
   x0_b = 0; y0_b = 0; x1_b = 640; y1_b = 480;
   for (pixel = 0; pixel < 307200; pixel = pixel + 1) begin
    pixel_valid = 1; frame_start = (pixel == 0);
    pixel_rgb_a = color_a; pixel_rgb_b = color_b;
    @(posedge clk); #1;
   end
   @(negedge clk); pixel_valid = 0; frame_start = 0;
   // Feature registers are captured on frame end, then consumed by matcher.
   repeat (2) @(posedge clk); #1;
   check(person_valid_a && person_valid_b, "both YOLOX-provided ROIs valid");
   check(feature_valid_a == 0 && feature_valid_b == 0, "feature valid pulses only at frame end");
   check(consecutive_hits == expected_hits, "expected confirmation streak");
   check(confirmed == expected_confirmed, "expected confirmation pulse");
  end
 endtask

 initial begin
  repeat (2) @(negedge clk);
  reset = 0;
  whole_frame(24'hff0000, 24'hee0000, 1, 0);
  whole_frame(24'hff0000, 24'hee0000, 2, 0);
  whole_frame(24'hff0000, 24'hee0000, 3, 1);
  whole_frame(24'hff0000, 24'h0000ff, 0, 0);
  $display("DUAL_CAMERA_ROI_MATCH_TOP_PASS checks=%0d", checks);
  $finish;
 end
 initial begin #20000000; $fatal(1, "Watchdog timeout"); end
endmodule
