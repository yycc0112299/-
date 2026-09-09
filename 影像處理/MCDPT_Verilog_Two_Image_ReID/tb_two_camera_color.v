`timescale 1ns / 1ps

module tb_two_camera_color;
    localparam W = 8;
    localparam H = 8;
    localparam N = W * H;
    localparam RGB = 24;

    reg [N*RGB-1:0] cam_a;
    reg [N*RGB-1:0] cam_b;

    wire ok_a, ok_b;
    wire [3:0] top_a, bot_a;
    wire [3:0] top_b, bot_b;
    wire [7:0] tp_a, bp_a;
    wire [7:0] tp_b, bp_b;
    wire [23:0] map_a, map_b;
    wire same;


    person_color_feature getA (
        .img(cam_a),
        .has_person(ok_a),
        .top_c(top_a), .bot_c(bot_a),
        .top_p(tp_a), .bot_p(bp_a),
        .fmap(map_a)
    );

    person_color_feature getB (
        .img(cam_b),
        .has_person(ok_b),
        .top_c(top_b), .bot_c(bot_b),
        .top_p(tp_b), .bot_p(bp_b),
        .fmap(map_b)
    );

    person_matcher cmp (
        .ok_a(ok_a), .f_a(map_a),
        .ok_b(ok_b), .f_b(map_b),
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

    function [RGB-1:0] man1;
        input integer p;
        begin
            case (p)
                10,11,12,13: man1 = pix(8'd235,8'd205,8'd170);
                18,19,20,21: man1 = pix(8'd40,8'd80,8'd210);
                26,27,28,29: man1 = pix(8'd35,8'd75,8'd205);
                34,35,36,37: man1 = pix(8'd190,8'd40,8'd40);
                42,43,44,45: man1 = pix(8'd185,8'd35,8'd35);
                50,51,52,53: man1 = pix(8'd185,8'd35,8'd35);
                default: man1 = pix(8'd8,8'd8,8'd8);
            endcase
        end
    endfunction

    function [RGB-1:0] man1_b;
        input integer p;
        begin
            case (p)
                10,11,12,13: man1_b = pix(8'd230,8'd200,8'd165);
                18,19,20,21: man1_b = pix(8'd45,8'd85,8'd215);
                26,27,28,29: man1_b = pix(8'd38,8'd78,8'd210);
                34,35,36,37: man1_b = pix(8'd195,8'd45,8'd45);
                42,43,44,45: man1_b = pix(8'd188,8'd38,8'd38);
                50,51,52,53: man1_b = pix(8'd188,8'd38,8'd38);
                default: man1_b = pix(8'd8,8'd8,8'd8);
            endcase
        end
    endfunction

    function [RGB-1:0] man2;
        input integer p;
        begin
            case (p)
                10,11,12,13: man2 = pix(8'd225,8'd210,8'd190);
                18,19,20,21: man2 = pix(8'd45,8'd190,8'd65);
                26,27,28,29: man2 = pix(8'd40,8'd185,8'd60);
                34,35,36,37: man2 = pix(8'd230,8'd225,8'd220);
                42,43,44,45: man2 = pix(8'd220,8'd220,8'd215);
                50,51,52,53: man2 = pix(8'd220,8'd220,8'd215);
                default: man2 = pix(8'd8,8'd8,8'd8);
            endcase
        end
    endfunction

    integer i;
    integer frame;

    initial begin
        for (frame = 0; frame < 3; frame = frame + 1) begin
            for (i = 0; i < N; i = i + 1) begin
                cam_a[i*RGB +: RGB] = man1(i);
                cam_b[i*RGB +: RGB] = man1_b(i);
            end

            #10;
            $display("frame %0d  A camera vs B camera, same person", frame);
            $display("A top=%0d bot=%0d  percent=%0d/%0d", top_a, bot_a, tp_a, bp_a);
            $display("B top=%0d bot=%0d  percent=%0d/%0d", top_b, bot_b, tp_b, bp_b);
            $display("same = %0d", same);

            if (same !== 1'b1) begin
                $display("ERROR frame same");
                $finish;
            end
        end


        for (i = 0; i < N; i = i + 1) begin
            cam_a[i*RGB +: RGB] = man1(i);
            cam_b[i*RGB +: RGB] = man2(i);
        end

        #10;
        $display("A camera vs B camera, different person");
        $display("A top=%0d bot=%0d  percent=%0d/%0d", top_a, bot_a, tp_a, bp_a);
        $display("B top=%0d bot=%0d  percent=%0d/%0d", top_b, bot_b, tp_b, bp_b);
        $display("same = %0d", same);

        if (same !== 1'b0) begin
            $display("ERROR different person");
            $finish;
        end

        $display("two camera color test ok");
        $finish;
    end
endmodule
