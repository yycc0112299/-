`include "mcdpt_defs.vh"
module tracker_fsm(
 input clk,rst,start,output [14:0] rom_addr_a,rom_addr_b,input [3:0] pixel_a,pixel_b,
 output [7:0] tracked_x,output [6:0] tracked_y,output track_done,output [1:0] status);
 localparam IDLE=4'd0,EXTRACT_REFERENCE=4'd1,SAVE_REFERENCE=4'd2,SEARCH_INIT=4'd3,
 EXTRACT_CANDIDATE=4'd4,CALC_DISTANCE=4'd5,COMPARE_MIN=4'd6,NEXT_CANDIDATE=4'd7,
 SEARCH_DONE=4'd8,DISPLAY_RESULT=4'd9;
 reg [3:0] state;reg ex_start,mem_we,sad_start,sc_init,sc_advance;
 wire ex_done,ex_busy,sad_done,last;wire [7:0] cand_x;wire [6:0] cand_y;wire [14:0] ex_addr;
 wire [3:0] mux_pixel;wire [63:0] ex_feat,ref_feat;wire [8:0] distance;
 reg [7:0] best_x;reg [6:0] best_y;reg [8:0] min_distance;
 wire ref_state=(state==EXTRACT_REFERENCE)||(state==SAVE_REFERENCE);
 assign rom_addr_a=ex_addr;assign rom_addr_b=ex_addr;assign mux_pixel=ref_state?pixel_a:pixel_b;
 assign tracked_x=best_x;assign tracked_y=best_y;assign track_done=(state==DISPLAY_RESULT);
 assign status=(state==IDLE||ref_state)?2'b00:((state==DISPLAY_RESULT)?2'b10:2'b01);
 feature_extractor ext(clk,rst,ex_start,ref_state?8'd30:cand_x,ref_state?7'd25:cand_y,ex_addr,mux_pixel,ex_feat,ex_done,ex_busy);
 feature_memory fmem(clk,mem_we,ex_feat,ref_feat);
 sad_matcher sad(clk,rst,sad_start,ref_feat,ex_feat,distance,sad_done);
 search_controller search(clk,rst,sc_init,sc_advance,cand_x,cand_y,last);
 always @(posedge clk)begin
   ex_start<=0;mem_we<=0;sad_start<=0;sc_init<=0;sc_advance<=0;
   if(rst)begin state<=IDLE;best_x<=0;best_y<=0;min_distance<=9'h1ff;end
   else case(state)
    IDLE:if(start)begin ex_start<=1;state<=EXTRACT_REFERENCE;end
    EXTRACT_REFERENCE:if(ex_done)state<=SAVE_REFERENCE;
    SAVE_REFERENCE:begin mem_we<=1;state<=SEARCH_INIT;end
    SEARCH_INIT:begin sc_init<=1;min_distance<=9'h1ff;state<=EXTRACT_CANDIDATE;end
    EXTRACT_CANDIDATE:if(!ex_busy)begin ex_start<=1;state<=CALC_DISTANCE;end
    CALC_DISTANCE:if(ex_done)begin sad_start<=1;state<=COMPARE_MIN;end
    COMPARE_MIN:if(sad_done)begin if(distance<min_distance)begin min_distance<=distance;best_x<=cand_x;best_y<=cand_y;end state<=last?SEARCH_DONE:NEXT_CANDIDATE;end
    NEXT_CANDIDATE:begin sc_advance<=1;state<=EXTRACT_CANDIDATE;end
    SEARCH_DONE:state<=DISPLAY_RESULT;
    DISPLAY_RESULT:if(start)begin ex_start<=1;state<=EXTRACT_REFERENCE;end
    default:state<=IDLE;
   endcase
 end
endmodule
