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

    function [RGB-1:0] face_a;
        input integer p;
        begin
            case (p)
                9,10,11,12,13,14: face_a = pix(8'd35,8'd25,8'd20);
                17,18,19,20,21,22: face_a = pix(8'd160,8'd110,8'd80);
                25,28: face_a = pix(8'd5,8'd5,8'd5);
                26,27,29,30: face_a = pix(8'd165,8'd115,8'd82);
                33,34,35,36,37,38: face_a = pix(8'd158,8'd108,8'd78);
                42,43,44,45: face_a = pix(8'd95,8'd25,8'd25);
                51,52,53,54: face_a = pix(8'd150,8'd100,8'd72);
                default: face_a = pix(8'd10,8'd10,8'd18);
            endcase
        end
    endfunction

    function [RGB-1:0] face_b;
        input integer p;
        begin
            case (p)
                9,10,11,12,13,14: face_b = pix(8'd38,8'd28,8'd21);
                17,18,19,20,21,22: face_b = pix(8'd166,8'd116,8'd86);
                25,28: face_b = pix(8'd6,8'd6,8'd6);
                26,27,29,30: face_b = pix(8'd170,8'd120,8'd88);
                33,34,35,36,37,38: face_b = pix(8'd162,8'd112,8'd82);
                42,43,44,45: face_b = pix(8'd98,8'd28,8'd28);
                51,52,53,54: face_b = pix(8'd154,8'd104,8'd75);
                default: face_b = pix(8'd10,8'd10,8'd18);
            endcase
        end
    endfunction

    function [RGB-1:0] face_c;
        input integer p;
        begin
            case (p)
                9,10,11,12,13,14: face_c = pix(8'd230,8'd220,8'd200);
                17,18,19,20,21,22: face_c = pix(8'd235,8'd225,8'd210);
                25,28: face_c = pix(8'd20,8'd20,8'd20);
                26,27,29,30: face_c = pix(8'd235,8'd225,8'd210);
                33,34,35,36,37,38: face_c = pix(8'd235,8'd225,8'd210);
                42,43,44,45: face_c = pix(8'd180,8'd60,8'd60);
                51,52,53,54: face_c = pix(8'd230,8'd220,8'd200);
                default: face_c = pix(8'd10,8'd10,8'd18);
            endcase
        end
    endfunction

    integer i;

    initial begin
        img_a = {N*RGB{1'b0}};

        img_b = {N*RGB{1'b0}};

        for (i = 0; i < N; i = i + 1) begin
            img_a[i*RGB +: RGB] = face_a(i);
            img_b[i*RGB +: RGB] = face_b(i);
        end

        #10;
        $display("case 1: two similar 8x8 faces");
        $display("  ......      ......");
        $display(" .HHHHHH.    .HHHHHH.");
        $display(" .FFFFFF.    .FFFFFF.");
        $display(" .EFEFFE.    .EFEFFE.");
        $display(" .FFFFFF.    .FFFFFF.");
        $display(" ..MMMM..    ..MMMM..");
        $display(" ...FFFF.    ...FFFF.");
        $display(" ........    ........");

        $display("feat_a = %h", feat_a);
        $display("feat_b = %h", feat_b);
        $display("dist = %0d", dist);
        $display("same = %0d", same);

        if (same !== 1'b1) begin
            $display("ERROR case 1");
            $finish;
        end


        for (i = 0; i < N; i = i + 1) begin
            img_a[i*RGB +: RGB] = face_a(i);
            img_b[i*RGB +: RGB] = face_c(i);
        end

        #10;
        $display("case 2: two different 8x8 faces");
        $display("  ......      ......");
        $display(" .HHHHHH.    .HHHHHH.");
        $display(" .FFFFFF.    .FFFFFF.");
        $display(" .EFEFFE.    .EFEFFE.");
        $display(" .FFFFFF.    .FFFFFF.");
        $display(" ..MMMM..    ..MMMM..");
        $display(" ...FFFF.    ...FFFF.");
        $display(" ........    ........");

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
