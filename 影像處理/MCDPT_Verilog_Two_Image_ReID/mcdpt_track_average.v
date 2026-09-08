`timescale 1ns / 1ps

module mcdpt_track_average #(
    parameter FEATURE_W = 8,
    parameter FEATURE_COUNT = 16
)(
    input clk,
    input rst,
    input update_en,
    input [FEATURE_COUNT*FEATURE_W-1:0] new_feature,
    output reg valid,
    output reg [FEATURE_COUNT*FEATURE_W-1:0] avg_feature
);

    integer i;
    reg [FEATURE_W-1:0] old_value;
    reg [FEATURE_W-1:0] new_value;
    reg [FEATURE_W+2:0] mixed_value;

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            valid <= 1'b0;
            avg_feature <= {FEATURE_COUNT*FEATURE_W{1'b0}};
        end else if (update_en) begin
            if (!valid) begin
                avg_feature <= new_feature;
                valid <= 1'b1;
            end else begin
                for (i = 0; i < FEATURE_COUNT; i = i + 1) begin
                    old_value = avg_feature[i*FEATURE_W +: FEATURE_W];
                    new_value = new_feature[i*FEATURE_W +: FEATURE_W];
                    mixed_value = (old_value * 3) + new_value;
                    avg_feature[i*FEATURE_W +: FEATURE_W] <= mixed_value >> 2;
                end
            end
        end
    end
endmodule
