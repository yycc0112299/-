`timescale 1ns / 1ps

module tb_brightness_matcher;
    localparam W = 8;
    localparam H = 8;
    localparam N = W * H;
    localparam RGB = 24;
    localparam FW = 8;
    localparam FN = 8;

    reg [N*RGB-1:0] img_a;
    reg [N*RGB-1:0] img_b;

    wire ok1;
    wire ok2;
    wire [FN*FW-1:0] feat_a;
    wire [FN*FW-1:0] feat_b;
    wire [15:0] dist;
    wire same;


    brightness_feature_extractor #(
        .W(W), .H(H), .N(N),
        .RGB(RGB), .FW(FW), .FN(FN)
    ) get_a (
        .img(img_a),
        .feat(feat_a),
        .has_obj(ok1)
    );


    brightness_feature_extractor #(
        .W(W), .H(H),
        .N(N), .RGB(RGB),
        .FW(FW), .FN(FN)
    ) get_b (
        .img(img_b), .feat(feat_b),
        .has_obj(ok2)
    );

    brightness_matcher #(
        .FW(FW), .FN(FN),
        .MATCH_TH(16'd190)
    ) cmp (
        .fa(feat_a),
        .ok1(ok1),
        .fb(feat_b),
        .ok2(ok2),
        .dist(dist),
        .same(same)
    );


    function [RGB-1:0] pix;
        input [7:0] r;
        input [7:0] g;
        input [7:0] b;
        begin
            pix = {r,g,b};
        end
    endfunction

    integer i;

    initial begin
        img_a = {N*RGB{1'b0}};

        img_b = {N*RGB{1'b0}};

        for (i = 0; i < N; i = i + 1) begin
            img_a[i*RGB +: RGB] = pix(8'd10,8'd10,8'd10);
            img_b[i*RGB +: RGB] = pix(8'd10,8'd10,8'd10);
        end

        for (i = 18; i < 46; i = i + 1) begin
            img_a[i*RGB +: RGB] = pix(8'd120,8'd120,8'd120);

            img_b[i*RGB +: RGB] = pix(8'd125,8'd125,8'd125);
        end

        #10;
        $display("case 1: close brightness");
        $display("feat_a = %h", feat_a);
        $display("feat_b = %h", feat_b);
        $display("dist = %0d", dist);
        $display("same = %0d", same);

        if (same !== 1'b1) begin
            $display("ERROR case 1");
            $finish;
        end


        for (i = 0; i < N; i = i + 1) begin
            img_a[i*RGB +: RGB] = pix(8'd10,8'd10,8'd10);
            img_b[i*RGB +: RGB] = pix(8'd10,8'd10,8'd10);
        end

        for (i = 18; i < 46; i = i + 1) begin
            img_a[i*RGB +: RGB] = pix(8'd120,8'd120,8'd120);

            img_b[i*RGB +: RGB] = pix(8'd220,8'd220,8'd220);
        end

        #10;
        $display("case 2: far brightness");
        $display("feat_a = %h", feat_a);
        $display("feat_b = %h", feat_b);
        $display("dist = %0d", dist);
        $display("same = %0d", same);

        if (same !== 1'b0) begin
            $display("ERROR case 2");
            $finish;
        end

        $display("brightness test ok");
        $finish;
    end
endmodule
