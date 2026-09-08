`include "mcdpt_defs.vh"
module feature_extractor(
  input clk,rst,start, input [7:0] base_x, input [6:0] base_y,
  output [14:0] rom_addr, input [3:0] pixel_in,
  output reg [63:0] features, output reg done, output busy);
  reg [9:0] sums[0:15];
  reg [10:0] issue_idx; reg [9:0] sample_idx;
  reg valid,active; reg [7:0] bx; reg [6:0] by;
  integer i,px,py,bi; reg [9:0] next_sum;
  assign busy=active;
  assign rom_addr=(issue_idx<1024)?((by+issue_idx/32)*`FRAME_W+bx+(issue_idx%32)):15'd0;
  always @(posedge clk) begin
    done<=1'b0;
    if(rst) begin active<=0;valid<=0;issue_idx<=0;features<=0;for(i=0;i<16;i=i+1)sums[i]<=0;end
    else if(start && !active) begin active<=1;valid<=0;issue_idx<=0;bx<=base_x;by<=base_y;for(i=0;i<16;i=i+1)sums[i]<=0;end
    else if(active) begin
      if(valid) begin
        px=sample_idx%32;py=sample_idx/32;bi=(py/8)*4+(px/8);next_sum=sums[bi]+pixel_in;sums[bi]<=next_sum;
        if((px%8)==7 && (py%8)==7) features[bi*4 +: 4]<=next_sum[9:6];
        if(sample_idx==1023) begin active<=0;valid<=0;done<=1;end
      end
      if(issue_idx<1024) begin sample_idx<=issue_idx[9:0];issue_idx<=issue_idx+1'b1;valid<=1;end
    end
  end
endmodule
