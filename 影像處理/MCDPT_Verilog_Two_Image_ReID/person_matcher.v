`timescale 1ns / 1ps

module person_matcher(
    input ok_a,
    input [23:0] f_a,
    input ok_b,
    input [23:0] f_b,
    output reg same
);

    wire [3:0] at = f_a[23:20];
    wire [3:0] ab = f_a[19:16];
    wire [7:0] ap1 = f_a[15:8];
    wire [7:0] ap2 = f_a[7:0];

    wire [3:0] bt = f_b[23:20];
    wire [3:0] bb = f_b[19:16];
    wire [7:0] bp1 = f_b[15:8];
    wire [7:0] bp2 = f_b[7:0];


    function [7:0] d8;
        input [7:0] x;
        input [7:0] y;
        begin
            d8 = (x >= y) ? (x-y) : (y-x);
        end
    endfunction

    always @* begin
        same = 1'b0;

        if (ok_a && ok_b) begin
            if ((at == bt) && (ab == bb)) begin
                if ((d8(ap1,bp1) < 8'd35) && (d8(ap2,bp2) < 8'd35))
                    same = 1'b1;
            end
        end
    end
endmodule
