`timescale 1ns / 1ps

module brightness_feature_extractor #(
    parameter W = 8,
    parameter H = 8,
    parameter N = W * H,
    parameter RGB = 24,
    parameter FW = 8,
    parameter FN = 8,
    parameter TH = 8'd30,
    parameter EDGE_TH = 8'd35
)(
    input  [N*RGB-1:0] img,
    output reg [FN*FW-1:0] feat,
    output reg has_obj
);

    integer x,y,k;

    reg [7:0] gray;
    reg [7:0] gray_r;
    reg [7:0] gray_d;

    reg [15:0] cnt;
    reg [15:0] hi_cnt;
    reg [15:0] low_cnt;
    reg [15:0] gray_total;
    reg [15:0] edge_cnt;
    reg [15:0] sx;
    reg [15:0] sy;


    function [7:0] rr;
        input integer p;
        begin
            rr = img[p*RGB+16 +: 8];
        end
    endfunction

    function [7:0] gg;
        input integer p;
        begin
            gg = img[p*RGB+8 +: 8];
        end
    endfunction

    function [7:0] bb;
        input integer p;
        begin
            bb = img[p*RGB +: 8];
        end
    endfunction

    function [7:0] lum;
        input [7:0] r;
        input [7:0] g;
        input [7:0] b;
        reg [15:0] tmp;
        begin
            tmp = (r * 8'd77) + (g * 8'd150) + (b * 8'd29);
            lum = tmp[15:8];
        end
    endfunction

    function [7:0] diff;
        input [7:0] a;
        input [7:0] b;
        begin
            diff = (a >= b) ? (a - b) : (b - a);
        end
    endfunction

    function [7:0] byte_lim;
        input [15:0] v;
        begin
            byte_lim = (v[15:8] != 8'd0) ? 8'hff : v[7:0];
        end
    endfunction


    always @(img) begin
        cnt = 16'd0;
        hi_cnt = 16'd0;
        low_cnt = 16'd0;
        gray_total = 16'd0;
        edge_cnt = 16'd0;
        sx = 16'd0;
        sy = 16'd0;
        feat = {FN*FW{1'b0}};
        has_obj = 1'b0;

        for (y = 0; y < H; y = y + 1) begin
            for (x = 0; x < W; x = x + 1) begin
                k = y * W + x;
                gray = lum(rr(k), gg(k), bb(k));

                if (gray >= TH) begin
                    cnt = cnt + 16'd1;
                    gray_total = gray_total + gray;
                    sx = sx + x[15:0];
                    sy = sy + y[15:0];

                    if (gray > 8'd170)
                        hi_cnt = hi_cnt + 16'd1;

                    if (gray < 8'd80)
                        low_cnt = low_cnt + 16'd1;


                    if (x < W - 1) begin
                        gray_r = lum(rr(k + 1), gg(k + 1), bb(k + 1));
                        if (diff(gray, gray_r) > EDGE_TH)
                            edge_cnt = edge_cnt + 16'd1;
                    end

                    if (y < H - 1) begin
                        gray_d = lum(rr(k + W), gg(k + W), bb(k + W));
                        if (diff(gray, gray_d) > EDGE_TH)
                            edge_cnt = edge_cnt + 16'd1;
                    end
                end
            end
        end

        has_obj = (cnt > 16'd6);

        if (cnt != 16'd0) begin
            feat[0*FW +: FW] = byte_lim(gray_total / cnt);
            feat[1*FW +: FW] = byte_lim(hi_cnt * 16'd4);
            feat[2*FW +: FW] = byte_lim(low_cnt * 16'd4);
            feat[3*FW +: FW] = byte_lim(edge_cnt * 16'd2);

            feat[4*FW +: FW] = byte_lim(cnt * 16'd4);
            feat[5*FW +: FW] = byte_lim((sx * 16'd32) / cnt);
            feat[6*FW +: FW] = byte_lim((sy * 16'd32) / cnt);
        end
    end
endmodule
