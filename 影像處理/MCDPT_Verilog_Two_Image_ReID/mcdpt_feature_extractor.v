`timescale 1ns / 1ps

module mcdpt_feature_extractor #(
    parameter IMG_W = 8,
    parameter IMG_H = 8,
    parameter PIXELS = IMG_W * IMG_H,
    parameter RGB_W = 24,
    parameter FEATURE_W = 8,
    parameter FEATURE_COUNT = 16,
    parameter FG_THRESHOLD = 8'd30,
    parameter EDGE_THRESHOLD = 8'd35
)(
    input  [PIXELS*RGB_W-1:0] image_rgb,
    output reg [FEATURE_COUNT*FEATURE_W-1:0] feature_vec,
    output reg person_present
);

    integer x;
    integer y;
    integer idx;

    reg [7:0] r;
    reg [7:0] g;
    reg [7:0] b;
    reg [7:0] gray;
    reg [7:0] right_gray;
    reg [7:0] down_gray;

    reg [15:0] fg_count;
    reg [15:0] bright_count;
    reg [15:0] dark_count;
    reg [15:0] upper_gray_sum;
    reg [15:0] lower_gray_sum;
    reg [15:0] all_gray_sum;
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

    function [7:0] to_gray;
        input [7:0] in_r;
        input [7:0] in_g;
        input [7:0] in_b;
        begin
            to_gray = (in_r + in_g + in_b) / 3;
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
        fg_count = 16'd0;
        bright_count = 16'd0;
        dark_count = 16'd0;
        upper_gray_sum = 16'd0;
        lower_gray_sum = 16'd0;
        all_gray_sum = 16'd0;
        edge_count = 16'd0;
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
                gray = to_gray(r, g, b);

                if (gray >= FG_THRESHOLD) begin
                    fg_count = fg_count + 16'd1;
                    all_gray_sum = all_gray_sum + gray;
                    x_sum = x_sum + x[15:0];
                    y_sum = y_sum + y[15:0];

                    if (y < (IMG_H / 2)) begin
                        upper_gray_sum = upper_gray_sum + gray;
                    end else begin
                        lower_gray_sum = lower_gray_sum + gray;
                    end

                    if (gray > 8'd170) begin
                        bright_count = bright_count + 16'd1;
                    end

                    if (gray < 8'd80) begin
                        dark_count = dark_count + 16'd1;
                    end

                    if (x < IMG_W - 1) begin
                        right_gray = to_gray(get_r(idx + 1), get_g(idx + 1), get_b(idx + 1));
                        if (abs_diff(gray, right_gray) > EDGE_THRESHOLD) begin
                            edge_count = edge_count + 16'd1;
                        end
                    end

                    if (y < IMG_H - 1) begin
                        down_gray = to_gray(get_r(idx + IMG_W), get_g(idx + IMG_W), get_b(idx + IMG_W));
                        if (abs_diff(gray, down_gray) > EDGE_THRESHOLD) begin
                            edge_count = edge_count + 16'd1;
                        end
                    end
                end
            end
        end

        person_present = (fg_count > 16'd6);

        if (fg_count != 16'd0) begin
            put_feature(0, all_gray_sum / fg_count);
            put_feature(1, upper_gray_sum / 16'd32);
            put_feature(2, lower_gray_sum / 16'd32);
            put_feature(3, bright_count * 16'd4);
            put_feature(4, dark_count * 16'd4);
            put_feature(5, edge_count * 16'd2);
            put_feature(6, fg_count * 16'd4);
            put_feature(7, (x_sum * 16'd32) / fg_count);
            put_feature(8, (y_sum * 16'd32) / fg_count);
        end
    end
endmodule
