`timescale 1ns/1ps
// Latches one committed YOLOX command exactly on its corresponding frame start.
// The video path sees stable bbox/person_detected values for the full frame.
module yolox_frame_command_adapter(
 input wire clk, input wire reset,
 input wire frame_start, input wire [31:0] stream_frame_id,
 input wire command_valid, input wire command_pair_present, input wire [31:0] command_frame_id,
 input wire [9:0] command_a_x0, command_a_y0, command_a_x1, command_a_y1,
 input wire [9:0] command_b_x0, command_b_y0, command_b_x1, command_b_y1,
 output reg command_accept, output reg frame_command_missing,
 output reg person_detected_a, person_detected_b,
 output reg [9:0] a_x0, a_y0, a_x1, a_y1, b_x0, b_y0, b_x1, b_y1
);
 always @(posedge clk) begin
  if (reset) begin
   command_accept<=0; frame_command_missing<=0; person_detected_a<=0; person_detected_b<=0;
   a_x0<=0; a_y0<=0; a_x1<=0; a_y1<=0; b_x0<=0; b_y0<=0; b_x1<=0; b_y1<=0;
  end else begin
   command_accept<=0;
   if (frame_start) begin
    frame_command_missing <= !(command_valid && command_frame_id==stream_frame_id);
    if (command_valid && command_frame_id==stream_frame_id) begin
     command_accept<=1; person_detected_a<=command_pair_present; person_detected_b<=command_pair_present;
     a_x0<=command_a_x0; a_y0<=command_a_y0; a_x1<=command_a_x1; a_y1<=command_a_y1;
     b_x0<=command_b_x0; b_y0<=command_b_y0; b_x1<=command_b_x1; b_y1<=command_b_y1;
    end else begin
     person_detected_a<=0; person_detected_b<=0;
    end
   end
  end
 end
endmodule
