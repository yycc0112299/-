`timescale 1ns/1ps
module color_feature_stream #(parameter W=640,H=480)(
 input clk,reset,pixel_valid,frame_start,
 input [23:0] pixel_rgb,
 output reg feature_valid,
 output reg [23:0] feature,
 output reg [31:0] pixel_count
);
 integer upper[0:7],lower[0:7];
 integer position,i,c,ct,cb,mt,mb;
 reg [7:0] pt,pb;
 function integer classify;
 input [23:0] pixel;
 integer r,g,b,mx,mn;
 begin
 r=pixel[23:16];g=pixel[15:8];b=pixel[7:0];
 mx=r;if(g>mx)mx=g;if(b>mx)mx=b;
 mn=r;if(g<mn)mn=g;if(b<mn)mn=b;
 if(mx<35)classify=0;
 else if(mx>=170 && mx-mn<45)classify=1;
 else if(r>140 && g>120 && b<90)classify=5;
 else if(r>g && g>b && r>80 && g-b>20)classify=6;
 else if(r>g+35 && r>b+35)classify=2;
 else if(g>r+30 && g>b+30)classify=3;
 else if(b>r+30 && b>g+30)classify=4;
 else classify=7;
 end
 endfunction
 // Pixel zero accompanies frame_start; valid gaps are allowed.
 always @(posedge clk) begin
 if(reset) begin
 feature_valid<=0;feature<=0;pixel_count<=0;position=0;
 for(i=0;i<8;i=i+1)begin upper[i]=0;lower[i]=0;end
 end else begin
 feature_valid<=0;
 if(pixel_valid) begin
 if(frame_start) begin
 position=0;
 for(i=0;i<8;i=i+1)begin upper[i]=0;lower[i]=0;end
 end
 if(position<W*H) begin
 c=classify(pixel_rgb);
 if(position<W*(H/2))upper[c]=upper[c]+1;
 else lower[c]=lower[c]+1;
 position=position+1;pixel_count<=position;
 if(position==W*H) begin
 ct=0;cb=0;mt=upper[0];mb=lower[0];
 for(i=1;i<8;i=i+1)begin
 if(upper[i]>mt)begin mt=upper[i];ct=i;end
 if(lower[i]>mb)begin mb=lower[i];cb=i;end
 end
 pt=(mt*100)/(W*(H/2));pb=(mb*100)/(W*(H-H/2));
 feature<={ct[3:0],cb[3:0],pt,pb};feature_valid<=1;
 end
 end
 end
 end
 end
endmodule
