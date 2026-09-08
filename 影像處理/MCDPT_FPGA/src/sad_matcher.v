module sad_matcher(input clk,rst,start,input [63:0] a,b,output reg [8:0] distance,output reg done);
  reg [3:0] idx;reg [8:0] acc;reg run;reg [3:0] av,bv;reg [4:0] diff;reg [8:0] next_acc;
  always @(posedge clk) begin
    done<=0;
    if(rst)begin run<=0;acc<=0;idx<=0;distance<=0;end
    else if(start&&!run)begin run<=1;acc<=0;idx<=0;end
    else if(run)begin
      av=a[idx*4 +: 4];bv=b[idx*4 +: 4];diff=(av>=bv)?av-bv:bv-av;next_acc=acc+diff;acc<=next_acc;
      if(idx==15)begin distance<=next_acc;done<=1;run<=0;end else idx<=idx+1'b1;
    end
  end
endmodule
