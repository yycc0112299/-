`timescale 1ns / 1ps

module mcdpt_two_image_reid_top #(
    parameter IMG_W = 8,
    parameter IMG_H = 8,
    parameter PIXELS = IMG_W * IMG_H,
    parameter RGB_W = 24,
    parameter FEATURE_W = 8,
    parameter FEATURE_COUNT = 16,
    parameter GLOBAL_MATCH_THRESH = 16'd190
)(
    input clk,
    input rst,
    input load_image_a,
    input load_image_b,
    input [PIXELS*RGB_W-1:0] image_a_rgb,
    input [PIXELS*RGB_W-1:0] image_b_rgb,
    output image_a_person_present,
    output image_b_person_present,
    output [FEATURE_COUNT*FEATURE_W-1:0] image_a_feature,
    output [FEATURE_COUNT*FEATURE_W-1:0] image_b_feature,
    output [FEATURE_COUNT*FEATURE_W-1:0] track_a_avg_feature,
    output [FEATURE_COUNT*FEATURE_W-1:0] track_b_avg_feature,
    output [15:0] global_distance,
    output same_person
);

    wire track_a_valid;
    wire track_b_valid;

    mcdpt_feature_extractor #(
        .IMG_W(IMG_W),
        .IMG_H(IMG_H),
        .PIXELS(PIXELS),
        .RGB_W(RGB_W),
        .FEATURE_W(FEATURE_W),
        .FEATURE_COUNT(FEATURE_COUNT)
    ) extractor_a (
        .image_rgb(image_a_rgb),
        .feature_vec(image_a_feature),
        .person_present(image_a_person_present)
    );

    mcdpt_feature_extractor #(
        .IMG_W(IMG_W),
        .IMG_H(IMG_H),
        .PIXELS(PIXELS),
        .RGB_W(RGB_W),
        .FEATURE_W(FEATURE_W),
        .FEATURE_COUNT(FEATURE_COUNT)
    ) extractor_b (
        .image_rgb(image_b_rgb),
        .feature_vec(image_b_feature),
        .person_present(image_b_person_present)
    );

    mcdpt_track_average #(
        .FEATURE_W(FEATURE_W),
        .FEATURE_COUNT(FEATURE_COUNT)
    ) track_a (
        .clk(clk),
        .rst(rst),
        .update_en(load_image_a && image_a_person_present),
        .new_feature(image_a_feature),
        .valid(track_a_valid),
        .avg_feature(track_a_avg_feature)
    );

    mcdpt_track_average #(
        .FEATURE_W(FEATURE_W),
        .FEATURE_COUNT(FEATURE_COUNT)
    ) track_b (
        .clk(clk),
        .rst(rst),
        .update_en(load_image_b && image_b_person_present),
        .new_feature(image_b_feature),
        .valid(track_b_valid),
        .avg_feature(track_b_avg_feature)
    );

    mcdpt_global_matcher #(
        .FEATURE_W(FEATURE_W),
        .FEATURE_COUNT(FEATURE_COUNT),
        .GLOBAL_MATCH_THRESH(GLOBAL_MATCH_THRESH)
    ) matcher (
        .local_avg_feature(track_a_avg_feature),
        .local_valid(track_a_valid),
        .remote_avg_feature(track_b_avg_feature),
        .remote_valid(track_b_valid),
        .distance(global_distance),
        .same_person(same_person)
    );
endmodule
