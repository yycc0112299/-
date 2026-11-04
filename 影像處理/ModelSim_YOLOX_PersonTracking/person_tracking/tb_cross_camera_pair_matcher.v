`timescale 1ns/1ps
module tb_cross_camera_pair_matcher;
 reg clk = 0;
 always #5 clk = ~clk;
 reg reset = 1, pair_observed = 0, a_valid = 0, b_valid = 0;
 reg [23:0] feature_a = 0, feature_b = 0;
 wire feature_similar, candidate_valid, confirmed;
 wire [1:0] consecutive_hits;
 integer checks = 0;

 cross_camera_pair_matcher dut(
  .clk(clk), .reset(reset), .pair_observed(pair_observed),
  .a_valid(a_valid), .b_valid(b_valid), .feature_a(feature_a), .feature_b(feature_b),
  .feature_similar(feature_similar), .candidate_valid(candidate_valid),
  .confirmed(confirmed), .consecutive_hits(consecutive_hits)
 );

 task check;
  input condition;
  input [511:0] label_text;
  begin
   if (condition !== 1'b1) begin
    $display("FAIL: %0s time=%0t hits=%0d candidate=%b confirmed=%b similar=%b",
             label_text, $time, consecutive_hits, candidate_valid, confirmed, feature_similar);
    $fatal(1, "Cross-camera matcher regression failed");
   end
   checks = checks + 1;
  end
 endtask

 task sample;
  input observed, av, bv;
  input [23:0] fa, fb;
  begin
   @(negedge clk);
   pair_observed = observed; a_valid = av; b_valid = bv; feature_a = fa; feature_b = fb;
   @(posedge clk); #1;
  end
 endtask

 initial begin
  repeat (2) @(negedge clk);
  reset = 0;
  // Same colors and a 35-point boundary difference: candidate, then confirm on hit 3.
  sample(1, 1, 1, 24'h226464, 24'h224141);
  check(feature_similar && candidate_valid && !confirmed && consecutive_hits == 1, "first candidate hit");
  sample(1, 1, 1, 24'h226464, 24'h224141);
  check(candidate_valid && !confirmed && consecutive_hits == 2, "second candidate hit");
  sample(1, 1, 1, 24'h226464, 24'h224141);
  check(candidate_valid && confirmed && consecutive_hits == 3, "third hit confirms pair");
  sample(1, 1, 1, 24'h226464, 24'h224141);
  check(candidate_valid && confirmed && consecutive_hits == 3, "confirmed pair saturates count");
  // A color mismatch breaks the streak and does not produce a candidate.
  sample(1, 1, 1, 24'h226464, 24'h246464);
  check(!feature_similar && !candidate_valid && !confirmed && consecutive_hits == 0, "color mismatch resets streak");
  // An observation gap also breaks continuity.
  sample(1, 1, 1, 24'h006464, 24'h006464);
  check(feature_similar && candidate_valid && consecutive_hits == 1, "black color feature remains valid");
  sample(0, 1, 1, 24'h006464, 24'h006464);
  check(feature_similar && !candidate_valid && !confirmed && consecutive_hits == 0, "missing pair resets streak");
  // A 36-point percentage mismatch is outside the allowed inclusive boundary.
  sample(1, 1, 1, 24'h226464, 24'h224040);
  check(!feature_similar && !candidate_valid && consecutive_hits == 0, "percentage mismatch rejected");
  sample(1, 0, 1, 24'h226464, 24'h226464);
  check(!feature_similar && !candidate_valid && consecutive_hits == 0, "invalid feature rejected");
  @(negedge clk); reset = 1;
  @(posedge clk); #1;
  check(!candidate_valid && !confirmed && consecutive_hits == 0, "reset clears state");
  $display("CROSS_CAMERA_PAIR_MATCHER_PASS checks=%0d", checks);
  $finish;
 end
 initial begin #10000; $fatal(1, "Watchdog timeout"); end
endmodule
