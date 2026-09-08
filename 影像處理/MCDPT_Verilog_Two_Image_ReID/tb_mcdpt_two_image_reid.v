`timescale 1ns / 1ps

module tb_mcdpt_two_image_reid;
    localparam IMG_W = 8;
    localparam IMG_H = 8;
    localparam PIXELS = IMG_W * IMG_H;
    localparam RGB_W = 24;

    reg clk;
    reg rst;
    reg load_image_a;
    reg load_image_b;
    reg [PIXELS*RGB_W-1:0] image_a_rgb;
    reg [PIXELS*RGB_W-1:0] image_b_rgb;

    wire image_a_person_present;
    wire image_b_person_present;
    wire [127:0] image_a_feature;
    wire [127:0] image_b_feature;
    wire [127:0] track_a_avg_feature;
    wire [127:0] track_b_avg_feature;
    wire [15:0] global_distance;
    wire same_person;

    mcdpt_two_image_reid_top dut (
        .clk(clk),
        .rst(rst),
        .load_image_a(load_image_a),
        .load_image_b(load_image_b),
        .image_a_rgb(image_a_rgb),
        .image_b_rgb(image_b_rgb),
        .image_a_person_present(image_a_person_present),
        .image_b_person_present(image_b_person_present),
        .image_a_feature(image_a_feature),
        .image_b_feature(image_b_feature),
        .track_a_avg_feature(track_a_avg_feature),
        .track_b_avg_feature(track_b_avg_feature),
        .global_distance(global_distance),
        .same_person(same_person)
    );

    always #5 clk = ~clk;

    task pack_pixel;
        input integer pixel_index;
        input [7:0] r;
        input [7:0] g;
        input [7:0] b;
        begin
            image_a_rgb[pixel_index*RGB_W +: RGB_W] = {r, g, b};
            image_b_rgb[pixel_index*RGB_W +: RGB_W] = {r, g, b};
        end
    endtask

    integer i;

    initial begin
        clk = 1'b0;
        rst = 1'b1;
        load_image_a = 1'b0;
        load_image_b = 1'b0;
        image_a_rgb = {PIXELS*RGB_W{1'b0}};
        image_b_rgb = {PIXELS*RGB_W{1'b0}};

        #20;
        rst = 1'b0;

        for (i = 0; i < PIXELS; i = i + 1) begin
            pack_pixel(i, 8'd10, 8'd10, 8'd10);
        end

        for (i = 18; i < 46; i = i + 1) begin
            image_a_rgb[i*RGB_W +: RGB_W] = {8'd150, 8'd70, 8'd55};
            image_b_rgb[i*RGB_W +: RGB_W] = {8'd142, 8'd75, 8'd62};
        end

        load_image_a = 1'b1;
        load_image_b = 1'b1;
        #10;
        load_image_a = 1'b0;
        load_image_b = 1'b0;
        #20;

        $display("case 1, similar person");
        $display("image_a_feature = %h", image_a_feature);
        $display("image_b_feature = %h", image_b_feature);
        $display("global_distance = %0d", global_distance);
        $display("same_person = %0d", same_person);

        if (same_person !== 1'b1) begin
            $display("ERROR: similar images should match");
            $finish;
        end

        rst = 1'b1;
        #10;
        rst = 1'b0;

        for (i = 0; i < PIXELS; i = i + 1) begin
            pack_pixel(i, 8'd10, 8'd10, 8'd10);
        end

        for (i = 18; i < 46; i = i + 1) begin
            image_a_rgb[i*RGB_W +: RGB_W] = {8'd150, 8'd70, 8'd55};
            image_b_rgb[i*RGB_W +: RGB_W] = {8'd30, 8'd60, 8'd190};
        end

        load_image_a = 1'b1;
        load_image_b = 1'b1;
        #10;
        load_image_a = 1'b0;
        load_image_b = 1'b0;
        #20;

        $display("case 2, different person");
        $display("image_a_feature = %h", image_a_feature);
        $display("image_b_feature = %h", image_b_feature);
        $display("global_distance = %0d", global_distance);
        $display("same_person = %0d", same_person);

        if (same_person !== 1'b0) begin
            $display("ERROR: different images should not match");
            $finish;
        end

        $display("MCDPT simplified Verilog test passed.");
        $finish;
    end
endmodule
