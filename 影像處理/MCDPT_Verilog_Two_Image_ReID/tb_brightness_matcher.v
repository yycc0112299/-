`timescale 1ns / 1ps

module tb_brightness_matcher;
    localparam IMG_W = 8;
    localparam IMG_H = 8;
    localparam PIXELS = IMG_W * IMG_H;
    localparam RGB_W = 24;
    localparam FEATURE_W = 8;
    localparam FEATURE_COUNT = 8;

    reg [PIXELS*RGB_W-1:0] image_a_rgb;
    reg [PIXELS*RGB_W-1:0] image_b_rgb;

    wire image_a_valid;
    wire image_b_valid;
    wire [FEATURE_COUNT*FEATURE_W-1:0] image_a_feature;
    wire [FEATURE_COUNT*FEATURE_W-1:0] image_b_feature;
    wire [15:0] match_distance;
    wire same_object;

    brightness_feature_extractor #(
        .IMG_W(IMG_W),
        .IMG_H(IMG_H),
        .PIXELS(PIXELS),
        .RGB_W(RGB_W),
        .FEATURE_W(FEATURE_W),
        .FEATURE_COUNT(FEATURE_COUNT)
    ) extractor_a (
        .image_rgb(image_a_rgb),
        .feature_vec(image_a_feature),
        .object_present(image_a_valid)
    );

    brightness_feature_extractor #(
        .IMG_W(IMG_W),
        .IMG_H(IMG_H),
        .PIXELS(PIXELS),
        .RGB_W(RGB_W),
        .FEATURE_W(FEATURE_W),
        .FEATURE_COUNT(FEATURE_COUNT)
    ) extractor_b (
        .image_rgb(image_b_rgb),
        .feature_vec(image_b_feature),
        .object_present(image_b_valid)
    );

    brightness_matcher #(
        .FEATURE_W(FEATURE_W),
        .FEATURE_COUNT(FEATURE_COUNT),
        .MATCH_THRESHOLD(16'd190)
    ) matcher (
        .feature_a(image_a_feature),
        .feature_a_valid(image_a_valid),
        .feature_b(image_b_feature),
        .feature_b_valid(image_b_valid),
        .distance(match_distance),
        .same_object(same_object)
    );

    function [RGB_W-1:0] rgb_pixel;
        input [7:0] r;
        input [7:0] g;
        input [7:0] b;
        begin
            rgb_pixel = {r, g, b};
        end
    endfunction

    integer i;

    initial begin
        image_a_rgb = {PIXELS*RGB_W{1'b0}};
        image_b_rgb = {PIXELS*RGB_W{1'b0}};

        for (i = 0; i < PIXELS; i = i + 1) begin
            image_a_rgb[i*RGB_W +: RGB_W] = rgb_pixel(8'd10, 8'd10, 8'd10);
            image_b_rgb[i*RGB_W +: RGB_W] = rgb_pixel(8'd10, 8'd10, 8'd10);
        end

        for (i = 18; i < 46; i = i + 1) begin
            image_a_rgb[i*RGB_W +: RGB_W] = rgb_pixel(8'd120, 8'd120, 8'd120);
            image_b_rgb[i*RGB_W +: RGB_W] = rgb_pixel(8'd125, 8'd125, 8'd125);
        end

        #10;
        $display("case 1, similar brightness");
        $display("image_a_feature = %h", image_a_feature);
        $display("image_b_feature = %h", image_b_feature);
        $display("match_distance = %0d", match_distance);
        $display("same_object = %0d", same_object);

        if (same_object !== 1'b1) begin
            $display("ERROR: similar brightness images should match");
            $finish;
        end

        for (i = 0; i < PIXELS; i = i + 1) begin
            image_a_rgb[i*RGB_W +: RGB_W] = rgb_pixel(8'd10, 8'd10, 8'd10);
            image_b_rgb[i*RGB_W +: RGB_W] = rgb_pixel(8'd10, 8'd10, 8'd10);
        end

        for (i = 18; i < 46; i = i + 1) begin
            image_a_rgb[i*RGB_W +: RGB_W] = rgb_pixel(8'd120, 8'd120, 8'd120);
            image_b_rgb[i*RGB_W +: RGB_W] = rgb_pixel(8'd220, 8'd220, 8'd220);
        end

        #10;
        $display("case 2, different brightness");
        $display("image_a_feature = %h", image_a_feature);
        $display("image_b_feature = %h", image_b_feature);
        $display("match_distance = %0d", match_distance);
        $display("same_object = %0d", same_object);

        if (same_object !== 1'b0) begin
            $display("ERROR: different brightness images should not match");
            $finish;
        end

        $display("Brightness matcher test passed.");
        $finish;
    end
endmodule
