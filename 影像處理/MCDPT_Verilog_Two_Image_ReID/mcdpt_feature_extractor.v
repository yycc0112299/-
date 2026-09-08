`timescale 1ns / 1ps

module mcdpt_feature_extractor #(
    parameter IMG_W = 8,
    parameter IMG_H = 8,
    parameter PIXELS = IMG_W * IMG_H,
    parameter RGB_W = 24,
    parameter FEATURE_W = 8,
    parameter FEATURE_COUNT = 16,
    parameter FG_THRESHOLD = 8'd30,
    parameter EDGE_THRESHOLD = 8'd45
)(
    input  [PIXELS*RGB_W-1:0] image_rgb,
    output reg [FEATURE_COUNT*FEATURE_W-1:0] feature_vec,
    output reg person_present
);

    integer x;
    integer y;
    integer idx;
    integer out_idx;

    reg [7:0] r;
    reg [7:0] g;
    reg [7:0] b;
    reg [7:0] max_ch;
    reg [7:0] min_ch;
    reg [7:0] right_r;
    reg [7:0] right_g;
    reg [7:0] right_b;
    reg [7:0] down_r;
    reg [7:0] down_g;
    reg [7:0] down_b;

    reg [15:0] upper_r;
    reg [15:0] upper_g;
    reg [15:0] upper_b;
    reg [15:0] lower_r;
    reg [15:0] lower_g;
    reg [15:0] lower_b;
    reg [15:0] dark_count;
    reg [15:0] bright_count;
    reg [15:0] red_dom_count;
    reg [15:0] green_dom_count;
    reg [15:0] blue_dom_count;
    reg [15:0] sat_sum;
    reg [15:0] edge_count;
    reg [15:0] fg_count;
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

    function [7:0] max3;
        input [7:0] a;
        input [7:0] c;
        input [7:0] d;
        begin
            max3 = (a >= c && a >= d) ? a : ((c >= d) ? c : d);
        end
    endfunction

    function [7:0] min3;
        input [7:0] a;
        input [7:0] c;
        input [7:0] d;
        begin
            min3 = (a <= c && a <= d) ? a : ((c <= d) ? c : d);
        end
    endfunction

    function [7:0] abs_diff;
        input [7:0] a;
        input [7:0] c;
        begin
            abs_diff = (a >= c) ? (a - c) : (c - a);
        end
    endfunction

    task put_feature;
        input integer feature_index;
        input [15:0] value;
        begin
            feature_vec[feature_index*FEATURE_W +: FEATURE_W] =
                (value[15:8] != 8'd0) ? 8'hff : value[7:0];
        end
    endtask

    always @(image_rgb) begin
        upper_r = 16'd0;
        upper_g = 16'd0;
        upper_b = 16'd0;
        lower_r = 16'd0;
        lower_g = 16'd0;
        lower_b = 16'd0;
        dark_count = 16'd0;
        bright_count = 16'd0;
        red_dom_count = 16'd0;
        green_dom_count = 16'd0;
        blue_dom_count = 16'd0;
        sat_sum = 16'd0;
        edge_count = 16'd0;
        fg_count = 16'd0;
        x_sum = 16'd0;
        y_sum = 16'd0;
        feature_vec = {FEATURE_COUNT*FEATURE_W{1'b0}};
        person_present = 1'b0;

        for (y = 0; y < IMG_H; y = y + 1) begin
            for (x = 0; x < IMG_W; x = x + 1) begin
                idx = y * IMG_W + x;
                r = get_r(idx);
                g = get_g(idx);
                b = get_b(idx);
                max_ch = max3(r, g, b);
                min_ch = min3(r, g, b);

                if (max_ch >= FG_THRESHOLD) begin
                    fg_count = fg_count + 16'd1;
                    x_sum = x_sum + x[15:0];
                    y_sum = y_sum + y[15:0];
                    sat_sum = sat_sum + (max_ch - min_ch);

                    if (y < (IMG_H / 2)) begin
                        upper_r = upper_r + r;
                        upper_g = upper_g + g;
                        upper_b = upper_b + b;
                    end else begin
                        lower_r = lower_r + r;
                        lower_g = lower_g + g;
                        lower_b = lower_b + b;
                    end

                    if (max_ch < 8'd80) begin
                        dark_count = dark_count + 16'd1;
                    end
                    if (max_ch > 8'd170) begin
                        bright_count = bright_count + 16'd1;
                    end
                    if (r > g + 8'd20 && r > b + 8'd20) begin
                        red_dom_count = red_dom_count + 16'd1;
                    end
                    if (g > r + 8'd20 && g > b + 8'd20) begin
                        green_dom_count = green_dom_count + 16'd1;
                    end
                    if (b > r + 8'd20 && b > g + 8'd20) begin
                        blue_dom_count = blue_dom_count + 16'd1;
                    end

                    if (x < IMG_W - 1) begin
                        right_r = get_r(idx + 1);
                        right_g = get_g(idx + 1);
                        right_b = get_b(idx + 1);
                        if (abs_diff(r, right_r) + abs_diff(g, right_g) + abs_diff(b, right_b) > EDGE_THRESHOLD) begin
                            edge_count = edge_count + 16'd1;
                        end
                    end

                    if (y < IMG_H - 1) begin
                        down_r = get_r(idx + IMG_W);
                        down_g = get_g(idx + IMG_W);
                        down_b = get_b(idx + IMG_W);
                        if (abs_diff(r, down_r) + abs_diff(g, down_g) + abs_diff(b, down_b) > EDGE_THRESHOLD) begin
                            edge_count = edge_count + 16'd1;
                        end
                    end
                end
            end
        end

        person_present = (fg_count > 16'd6);

        if (fg_count != 16'd0) begin
            put_feature(0,  upper_r / 16'd32);
            put_feature(1,  upper_g / 16'd32);
            put_feature(2,  upper_b / 16'd32);
            put_feature(3,  lower_r / 16'd32);
            put_feature(4,  lower_g / 16'd32);
            put_feature(5,  lower_b / 16'd32);
            put_feature(6,  dark_count * 16'd4);
            put_feature(7,  bright_count * 16'd4);
            put_feature(8,  red_dom_count * 16'd4);
            put_feature(9,  green_dom_count * 16'd4);
            put_feature(10, blue_dom_count * 16'd4);
            put_feature(11, sat_sum / fg_count);
            put_feature(12, edge_count * 16'd2);
            put_feature(13, fg_count * 16'd4);
            put_feature(14, (x_sum * 16'd32) / fg_count);
            put_feature(15, (y_sum * 16'd32) / fg_count);
        end
    end
endmodule
