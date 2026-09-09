`timescale 1ns / 1ps

module person_color_feature #(
    parameter W = 8,
    parameter H = 8,
    parameter N = W * H,
    parameter RGB = 24
)(
    input [N*RGB-1:0] img,
    output reg has_person,
    output reg [3:0] top_c,
    output reg [3:0] bot_c,
    output reg [7:0] top_p,
    output reg [7:0] bot_p,
    output reg [23:0] fmap
);

    integer x,y,p;
    reg [3:0] c;

    reg [7:0] t0,t1,t2,t3,t4,t5,t6,t7;
    reg [7:0] b0,b1,b2,b3,b4,b5,b6,b7;
    reg [7:0] tc,bc;


    function [7:0] rr;
        input integer k;
        begin
            rr = img[k*RGB+16 +: 8];
        end
    endfunction

    function [7:0] gg;
        input integer k;
        begin
            gg = img[k*RGB+8 +: 8];
        end
    endfunction

    function [7:0] bb;
        input integer k;
        begin
            bb = img[k*RGB +: 8];
        end
    endfunction

    function [7:0] abs1;
        input [7:0] a;
        input [7:0] b;
        begin
            abs1 = (a >= b) ? (a-b) : (b-a);
        end
    endfunction

    function [3:0] color8;
        input [7:0] r;
        input [7:0] g;
        input [7:0] b;
        reg [7:0] mx;
        reg [7:0] mn;
        begin
            mx = r;
            if (g > mx) mx = g;
            if (b > mx) mx = b;

            mn = r;
            if (g < mn) mn = g;
            if (b < mn) mn = b;

            if (mx < 8'd35)
                color8 = 4'd0;
            else if ((mx > 8'd170) && (abs1(mx,mn) < 8'd45))
                color8 = 4'd1;
            else if ((r > g + 8'd35) && (r > b + 8'd35))
                color8 = 4'd2;
            else if ((g > r + 8'd30) && (g > b + 8'd30))
                color8 = 4'd3;
            else if ((b > r + 8'd30) && (b > g + 8'd30))
                color8 = 4'd4;
            else if ((r > 8'd140) && (g > 8'd120) && (b < 8'd90))
                color8 = 4'd5;
            else if ((r > g) && (g > b) && (r > 8'd80))
                color8 = 4'd6;
            else
                color8 = 4'd7;
        end
    endfunction

    function [3:0] big_color;
        input [7:0] c0;
        input [7:0] c1;
        input [7:0] c2;
        input [7:0] c3;
        input [7:0] c4;
        input [7:0] c5;
        input [7:0] c6;
        input [7:0] c7;
        reg [7:0] best;
        begin
            best = c1;
            big_color = 4'd1;

            if (c2 > best) begin best = c2; big_color = 4'd2; end
            if (c3 > best) begin best = c3; big_color = 4'd3; end
            if (c4 > best) begin best = c4; big_color = 4'd4; end
            if (c5 > best) begin best = c5; big_color = 4'd5; end
            if (c6 > best) begin best = c6; big_color = 4'd6; end
            if (c7 > best) begin best = c7; big_color = 4'd7; end
            if ((c0 > best) && (best == 8'd0)) big_color = 4'd0;
        end
    endfunction

    function [7:0] get_cnt;
        input [3:0] id;
        input [7:0] c0;
        input [7:0] c1;
        input [7:0] c2;
        input [7:0] c3;
        input [7:0] c4;
        input [7:0] c5;
        input [7:0] c6;
        input [7:0] c7;
        begin
            case (id)
                4'd0: get_cnt = c0;
                4'd1: get_cnt = c1;
                4'd2: get_cnt = c2;
                4'd3: get_cnt = c3;
                4'd4: get_cnt = c4;
                4'd5: get_cnt = c5;
                4'd6: get_cnt = c6;
                default: get_cnt = c7;
            endcase
        end
    endfunction


    always @(img) begin
        t0=0; t1=0; t2=0; t3=0; t4=0; t5=0; t6=0; t7=0;
        b0=0; b1=0; b2=0; b3=0; b4=0; b5=0; b6=0; b7=0;
        tc = 0; bc = 0;

        for (y = 0; y < H; y = y + 1) begin
            for (x = 0; x < W; x = x + 1) begin
                p = y*W + x;
                c = color8(rr(p), gg(p), bb(p));

                if (c != 4'd0) begin
                    if (y < H/2) begin
                        tc = tc + 1;
                        case (c)
                            4'd1: t1 = t1 + 1;
                            4'd2: t2 = t2 + 1;
                            4'd3: t3 = t3 + 1;
                            4'd4: t4 = t4 + 1;
                            4'd5: t5 = t5 + 1;
                            4'd6: t6 = t6 + 1;
                            default: t7 = t7 + 1;
                        endcase
                    end else begin
                        bc = bc + 1;
                        case (c)
                            4'd1: b1 = b1 + 1;
                            4'd2: b2 = b2 + 1;
                            4'd3: b3 = b3 + 1;
                            4'd4: b4 = b4 + 1;
                            4'd5: b5 = b5 + 1;
                            4'd6: b6 = b6 + 1;
                            default: b7 = b7 + 1;
                        endcase
                    end
                end
            end
        end

        top_c = big_color(t0,t1,t2,t3,t4,t5,t6,t7);
        bot_c = big_color(b0,b1,b2,b3,b4,b5,b6,b7);

        if (tc != 0)
            top_p = (get_cnt(top_c,t0,t1,t2,t3,t4,t5,t6,t7) * 16'd100) / tc;
        else
            top_p = 0;

        if (bc != 0)
            bot_p = (get_cnt(bot_c,b0,b1,b2,b3,b4,b5,b6,b7) * 16'd100) / bc;
        else
            bot_p = 0;

        has_person = ((tc + bc) > 8'd10) && (tc != 0) && (bc != 0);
        fmap = {top_c, bot_c, top_p, bot_p};
    end
endmodule
