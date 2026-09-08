`timescale 1ns / 1ps

module mcdpt_global_matcher #(
    parameter FEATURE_W = 8,
    parameter FEATURE_COUNT = 16,
    parameter DIST_W = 16,
    parameter GLOBAL_MATCH_THRESH = 16'd190
)(
    input [FEATURE_COUNT*FEATURE_W-1:0] local_avg_feature,
    input local_valid,
    input [FEATURE_COUNT*FEATURE_W-1:0] remote_avg_feature,
    input remote_valid,
    output [DIST_W-1:0] distance,
    output same_person
);

    mcdpt_feature_distance #(
        .FEATURE_W(FEATURE_W),
        .FEATURE_COUNT(FEATURE_COUNT),
        .DIST_W(DIST_W)
    ) distance_unit (
        .feature_a(local_avg_feature),
        .feature_b(remote_avg_feature),
        .distance(distance)
    );

    assign same_person = local_valid && remote_valid && (distance <= GLOBAL_MATCH_THRESH);
endmodule
