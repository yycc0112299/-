`timescale 1ns / 1ps

module brightness_matcher #(
    parameter FEATURE_W = 8,
    parameter FEATURE_COUNT = 8,
    parameter DIST_W = 16,
    parameter MATCH_THRESHOLD = 16'd190
)(
    input [FEATURE_COUNT*FEATURE_W-1:0] feature_a,
    input feature_a_valid,
    input [FEATURE_COUNT*FEATURE_W-1:0] feature_b,
    input feature_b_valid,
    output [DIST_W-1:0] distance,
    output same_object
);

    feature_distance #(
        .FEATURE_W(FEATURE_W),
        .FEATURE_COUNT(FEATURE_COUNT),
        .DIST_W(DIST_W)
    ) distance_unit (
        .feature_a(feature_a),
        .feature_b(feature_b),
        .distance(distance)
    );

    assign same_object = feature_a_valid && feature_b_valid && (distance <= MATCH_THRESHOLD);
endmodule
