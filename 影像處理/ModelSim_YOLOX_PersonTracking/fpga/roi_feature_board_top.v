`timescale 1ns/1ps
// Board-neutral wrapper for the existing 640x480 ROI feature RTL.
// Add a PYNQ-Z2 or EGo1 pin/clock adapter around this module when the board is connected.
module roi_feature_board_top #(
    parameter IMAGE_WIDTH = 640,
    parameter IMAGE_HEIGHT = 480
) (
    input wire clk,
    input wire reset,
    input wire pixel_valid,
    input wire frame_start,
    input wire person_detected,
    input wire [23:0] pixel_rgb,
    input wire [9:0] x0, y0, x1, y1,
    output wire feature_valid,
    output wire person_valid,
    output wire [23:0] feature,
    output wire [31:0] top_pixels,
    output wire [31:0] bottom_pixels,
    output wire [31:0] pixel_count,
    output wire result_led
);
    person_roi_stream roi (
        .clk(clk), .reset(reset), .pixel_valid(pixel_valid),
        .frame_start(frame_start), .person_detected(person_detected),
        .pixel_rgb(pixel_rgb), .x0(x0), .y0(y0), .x1(x1), .y1(y1),
        .feature_valid(feature_valid), .person_valid(person_valid),
        .feature(feature), .top_pixels(top_pixels),
        .bottom_pixels(bottom_pixels), .pixel_count(pixel_count)
    );

    assign result_led = feature_valid && person_valid;
endmodule
