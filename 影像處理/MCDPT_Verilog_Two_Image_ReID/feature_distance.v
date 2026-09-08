`timescale 1ns / 1ps

module feature_distance #(
    parameter FW = 8,
    parameter FN = 8,
    parameter DW = 16
)(
    input  [FN*FW-1:0] fa,
    input  [FN*FW-1:0] fb,
    output reg [DW-1:0] dist
);

    integer i;
    reg [FW-1:0] a;
    reg [FW-1:0] b;
    reg [FW:0] d;


    always @* begin
        dist = {DW{1'b0}};

        for (i = 0; i < FN; i = i + 1) begin
            a = fa[i*FW +: FW];
            b = fb[i*FW +: FW];

            d = (a >= b) ? (a - b) : (b - a);
            dist = dist + d;
        end
    end
endmodule
