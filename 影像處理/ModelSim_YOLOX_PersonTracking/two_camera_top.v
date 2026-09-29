`timescale 1ns/1ps
// One corresponding ROI pair per frame_valid pulse. Upstream supplies
// detection, tracking IDs, cropping and synchronization of the two cameras.
module two_camera_top #(parameter W=8,H=8,MAX_PERCENT_DIFF=35)(
    input clk, reset,
    input frame_valid,
    input [31:0] frame_id,
    input [W*H*24-1:0] image_a,image_b,
    input [W*H-1:0] mask_a,mask_b,
    input detected_a,detected_b,
    output reg result_valid,
    output reg [31:0] result_frame_id,
    output reg valid_a,valid_b,
    output reg [23:0] feature_a,feature_b,
    output reg same_person
);
    wire va,vb;
    wire [23:0] fa,fb;
    color_feature #(W,H) a(image_a,mask_a,detected_a,va,fa);
    color_feature #(W,H) b(image_b,mask_b,detected_b,vb,fb);
    function integer difference;
        input [7:0] x,y;
        begin if(x>=y) difference=x-y; else difference=y-x; end
    endfunction
    always @(posedge clk) begin
        if(reset) begin
            result_valid<=0; result_frame_id<=0;
            valid_a<=0; valid_b<=0; feature_a<=0; feature_b<=0;
            same_person<=0;
        end else begin
            result_valid<=frame_valid;
            if(frame_valid) begin
                result_frame_id<=frame_id;
                valid_a<=va; valid_b<=vb; feature_a<=fa; feature_b<=fb;
                same_person<=va && vb && fa[23:16]==fb[23:16]
                    && difference(fa[15:8],fb[15:8])<=MAX_PERCENT_DIFF
                    && difference(fa[7:0],fb[7:0])<=MAX_PERCENT_DIFF;
            end
        end
    end
endmodule
