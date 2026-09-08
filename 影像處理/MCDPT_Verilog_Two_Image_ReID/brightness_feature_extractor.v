`timescale 1ns / 1ps

module brightness_feature_extractor #(
    parameter IMG_W = 8,
    parameter IMG_H = 8,
    parameter PIXELS = IMG_W * IMG_H,
    parameter RGB_W = 24,
    parameter FEATURE_W = 8,
    parameter FEATURE_COUNT = 8,
    parameter FG_THRESHOLD = 8'd30,
    parameter EDGE_THRESHOLD = 8'd35
)(
    input  [PIXELS*RGB_W-1:0] image_rgb,
    output reg [FEATURE_COUNT*FEATURE_W-1:0] feature_vec,
    output reg object_present
);

    integer x;
    integer y;
    integer idx;

    reg [7:0] gray;
    reg [7:0] right_gray;
    reg [7:0] down_gray;

    reg [15:0] fg_count;
    reg [15:0] bright_count;
    reg [15:0] dark_count;
    reg [15:0] gray_sum;
    reg [15:0] edge_count;
    reg [15:0] x_sum;
    reg [15:0] y_sum;

    function [7:0] get_r;
        input integer pixel_index;
        begin
            get_r = image_rgb[pixel_index*RGB_W+16 +: 8];
        end
    endfunction

    function [7:0] get_g;
        input integer pixel_index;
        begin
            get_g = image_rgb[pixel_index*RGB_W+8 +: 8];
        end
    endfunction

    function [7:0] get_b;
        input integer pixel_index;
        begin
            get_b = image_rgb[pixel_index*RGB_W +: 8];
        end
    endfunction

    function [7:0] rgb_to_brightness;
        input [7:0] in_r;
        input [7:0] in_g;
        input [7:0] in_b;
        reg [15:0] y_value;
        begin
            y_value = (in_r * 8'd77) + (in_g * 8'd150) + (in_b * 8'd29);
            rgb_to_brightness = y_value[15:8];
        end
    endfunction

    function [7:0] abs_diff;
        input [7:0] a;
        input [7:0] b;
        begin
            abs_diff = (a >= b) ? (a - b) : (b - a);
        end
    endfunction

    function [7:0] limit_to_byte;
        input [15:0] value;
        begin
            limit_to_byte = (value[15:8] != 8'd0) ? 8'hff : value[7:0];
        end
    endfunction

    always @(image_rgb) begin
        fg_count = 16'd0;
        bright_count = 16'd0;
        dark_count = 16'd0;
        gray_sum = 16'd0;
        edge_count = 16'd0;
        x_sum = 16'd0;
        y_sum = 16'd0;
        feature_vec = {FEATURE_COUNT*FEATURE_W{1'b0}};
        object_present = 1'b0;

        for (y = 0; y < IMG_H; y = y + 1) begin
            for (x = 0; x < IMG_W; x = x + 1) begin
                idx = y * IMG_W + x;
                gray = rgb_to_brightness(get_r(idx), get_g(idx), get_b(idx));

                if (gray >= FG_THRESHOLD) begin
                    fg_count = fg_count + 16'd1;
                    gray_sum = gray_sum + gray;
                    x_sum = x_sum + x[15:0];
                    y_sum = y_sum + y[15:0];

                    if (gray > 8'd170) begin
                        bright_count = bright_count + 16'd1;
                    end

                    if (gray < 8'd80) begin
                        dark_count = dark_count + 16'd1;
                    end

                    if (x < IMG_W - 1) begin
                        right_gray = rgb_to_brightness(get_r(idx + 1), get_g(idx + 1), get_b(idx + 1));
                        if (abs_diff(gray, right_gray) > EDGE_THRESHOLD) begin
                            edge_count = edge_count + 16'd1;
                        end
                    end

                    if (y < IMG_H - 1) begin
                        down_gray = rgb_to_brightness(get_r(idx + IMG_W), get_g(idx + IMG_W), get_b(idx + IMG_W));
                        if (abs_diff(gray, down_gray) > EDGE_THRESHOLD) begin
                            edge_count = edge_count + 16'd1;
                        end
                    end
                end
            end
        end

        object_present = (fg_count > 16'd6);

        if (fg_count != 16'd0) begin
            feature_vec[0*FEATURE_W +: FEATURE_W] = limit_to_byte(gray_sum / fg_count);
            feature_vec[1*FEATURE_W +: FEATURE_W] = limit_to_byte(bright_count * 16'd4);
            feature_vec[2*FEATURE_W +: FEATURE_W] = limit_to_byte(dark_count * 16'd4);
            feature_vec[3*FEATURE_W +: FEATURE_W] = limit_to_byte(edge_count * 16'd2);
            feature_vec[4*FEATURE_W +: FEATURE_W] = limit_to_byte(fg_count * 16'd4);
            feature_vec[5*FEATURE_W +: FEATURE_W] = limit_to_byte((x_sum * 16'd32) / fg_count);
            feature_vec[6*FEATURE_W +: FEATURE_W] = limit_to_byte((y_sum * 16'd32) / fg_count);
        end
    end
endmodule
