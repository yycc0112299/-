`timescale 1ns / 1ps

module feature_distance #(
    parameter FEATURE_W = 8,
    parameter FEATURE_COUNT = 8,
    parameter DIST_W = 16
)(
    input  [FEATURE_COUNT*FEATURE_W-1:0] feature_a,
    input  [FEATURE_COUNT*FEATURE_W-1:0] feature_b,
    output reg [DIST_W-1:0] distance
);

    integer i;
    reg [FEATURE_W-1:0] a_value;
    reg [FEATURE_W-1:0] b_value;
    reg [FEATURE_W:0] diff;
    reg [DIST_W-1:0] running_sum;

    always @* begin
        running_sum = {DIST_W{1'b0}};

        for (i = 0; i < FEATURE_COUNT; i = i + 1) begin
            a_value = feature_a[i*FEATURE_W +: FEATURE_W];
            b_value = feature_b[i*FEATURE_W +: FEATURE_W];
            diff = (a_value >= b_value) ? (a_value - b_value) : (b_value - a_value);
            running_sum = running_sum + diff;
        end

        distance = running_sum;
    end
endmodule
