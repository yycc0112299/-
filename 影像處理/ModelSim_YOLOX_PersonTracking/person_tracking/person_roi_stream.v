`timescale 1ns/1ps
module person_roi_stream(
 input clk,reset,pixel_valid,frame_start,person_detected,
 input [23:0] pixel_rgb,
 input [9:0] x0,y0,x1,y1,
 output reg feature_valid,person_valid,
 output reg [23:0] feature,
 output reg [31:0] top_pixels,bottom_pixels,pixel_count
);
 integer upper[0:7],lower[0:7];
 integer x,y,n,i,c,ct,cb,mt,mb,nt,nb;
 reg [7:0] pt,pb;
 function integer classify;
 input [23:0] p;
 integer r,g,b,mx,mn;
 begin
 r=p[23:16];g=p[15:8];b=p[7:0];
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
 always @(posedge clk)begin
 if(reset)begin
 feature_valid<=0;person_valid<=0;feature<=0;top_pixels<=0;bottom_pixels<=0;pixel_count<=0;
 x=0;y=0;n=0;nt=0;nb=0;
 for(i=0;i<8;i=i+1)begin upper[i]=0;lower[i]=0;end
 end else begin
 feature_valid<=0;
 if(pixel_valid)begin
 if(frame_start)begin
 x=0;y=0;n=0;nt=0;nb=0;
 for(i=0;i<8;i=i+1)begin upper[i]=0;lower[i]=0;end
 end
 if(n<307200)begin
 if(person_detected && x>=x0 && x<x1 && y>=y0 && y<y1)begin
 c=classify(pixel_rgb);
 if(y<y0+(y1-y0)/2)begin upper[c]=upper[c]+1;nt=nt+1;end
 else begin lower[c]=lower[c]+1;nb=nb+1;end
 end
 n=n+1;pixel_count<=n;
 if(x==639)begin x=0;y=y+1;end else x=x+1;
 if(n==307200)begin
 feature_valid<=1;top_pixels<=nt;bottom_pixels<=nb;
 person_valid<=person_detected && nt>0 && nb>0;feature<=0;
 if(person_detected && nt>0 && nb>0)begin
 ct=0;cb=0;mt=upper[0];mb=lower[0];
 for(i=1;i<8;i=i+1)begin
 if(upper[i]>mt)begin mt=upper[i];ct=i;end
 if(lower[i]>mb)begin mb=lower[i];cb=i;end
 end
 pt=mt*100/nt;pb=mb*100/nb;
 feature<={ct[3:0],cb[3:0],pt,pb};
 end
 end
 end
 end
 end
 end
endmodule
