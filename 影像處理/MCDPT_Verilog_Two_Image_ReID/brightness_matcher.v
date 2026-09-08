`timescale 1ns / 1ps

module brightness_matcher #(
    parameter FW = 8,
    parameter FN = 8,
    parameter DW = 16,
    parameter MATCH_TH = 16'd190
)(
    input [FN*FW-1:0] fa,
    input ok_a,
    input [FN*FW-1:0] fb,
    input ok_b,
    output [DW-1:0] dist,
    output same
);

    feature_distance #(
        .FW(FW),
        .FN(FN),
        .DW(DW)
    ) u_dist (
        .fa(fa),
        .fb(fb),
        .dist(dist)
    );

    assign same = ok_a && ok_b && (dist <= MATCH_TH);
endmodule
