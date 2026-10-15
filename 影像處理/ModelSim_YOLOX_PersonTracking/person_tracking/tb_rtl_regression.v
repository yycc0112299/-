`timescale 1ns/1ps
module tb_rtl_regression;
reg clk=0;
always #5 clk=~clk;
reg reset=1,pixel_valid=0,frame_start=0,person_detected=0;
reg [23:0] pixel_rgb=0;
reg [9:0] x0=0,y0=0,x1=0,y1=0;
wire feature_valid,person_valid;
wire [23:0] feature;
wire [31:0] top_pixels,bottom_pixels,pixel_count;
reg previous_valid=0,current_valid=0;
reg [23:0] previous_feature=0,current_feature=0;
wire color_similar;
integer checks=0,frames=0,k,xx,yy;
person_roi_stream dut(clk,reset,pixel_valid,frame_start,person_detected,
 pixel_rgb,x0,y0,x1,y1,feature_valid,person_valid,feature,
 top_pixels,bottom_pixels,pixel_count);
person_feature_compare cmp(previous_valid,current_valid,previous_feature,
 current_feature,color_similar);
task check;
 input condition;
 input [511:0] label_text;
 begin
 if(condition !== 1'b1) begin
 $display("FAIL: %0s time=%0t feature=%h top=%0d bottom=%0d count=%0d",
 label_text,$time,feature,top_pixels,bottom_pixels,pixel_count);
 $fatal(1,"RTL regression failed");
 end
 checks=checks+1;
 end
endtask
// Coordinates are half-open. Expected answers below are hand calculated.
// mode 0: red; mode 1: red above ROI midpoint, blue below; mode 2: black.
task frame;
 input integer ax,ay,bx,by,detected,mode,stalls;
 input integer expected_top,expected_bottom,expected_valid;
 input [23:0] expected_feature;
 begin
 @(negedge clk);
 x0=ax;y0=ay;x1=bx;y1=by;person_detected=detected;
 for(k=0;k<307200;k=k+1) begin
 if(stalls && k%8191==0) begin
 pixel_valid=0;frame_start=0;
 @(posedge clk);#1;
 check(!feature_valid,"no output during stalled input");
 @(negedge clk);
 end
 xx=k%640;yy=k/640;
 pixel_valid=1;frame_start=(k==0);
 if(mode==2) pixel_rgb=24'h000000;
 else if(mode==1 && yy>=ay+(by-ay)/2) pixel_rgb=24'h0000ff;
 else pixel_rgb=24'hff0000;
 @(posedge clk);#1;
 if(k==307199) begin
 check(feature_valid,"output on final accepted pixel");
 check(pixel_count==307200,"full frame count");
 check(top_pixels==expected_top && bottom_pixels==expected_bottom,"ROI area");
 check(person_valid==expected_valid,"person validity");
 check(feature===expected_feature,"hand calculated feature");
 end else if(feature_valid) $fatal(1,"Premature output at pixel %0d",k);
 @(negedge clk);
 end
 pixel_valid=0;frame_start=0;
 @(posedge clk);#1;check(!feature_valid,"single cycle valid pulse");
 frames=frames+1;
 $display("FRAME_PASS %0d feature=%h",frames,feature);
 end
endtask
task compare_case;
 input pv,cv;
 input [23:0] a,b;
 input expected;
 begin
 previous_valid=pv;current_valid=cv;previous_feature=a;current_feature=b;
 #1;check(color_similar===expected,"feature compare boundary");
 end
endtask
initial begin
 repeat(3) @(negedge clk);
 reset=0;
 frame(0,0,640,480,1,0,0,153600,153600,1,24'h226464);
 frame(10,20,14,25,1,1,1,8,12,1,24'h246464);
 frame(639,478,640,480,1,0,0,1,1,1,24'h226464);
 frame(0,0,640,480,0,0,0,0,0,0,24'h000000);
 frame(20,20,20,40,1,0,0,0,0,0,24'h000000);
 frame(10,10,14,11,1,0,0,0,4,0,24'h000000);
 frame(0,0,640,480,1,2,0,153600,153600,1,24'h006464);
 compare_case(1,1,24'h226464,24'h226464,1);
 compare_case(1,1,24'h226464,24'h224141,1);
 compare_case(1,1,24'h226464,24'h224040,0);
 compare_case(1,1,24'h224141,24'h226464,1);
 compare_case(1,1,24'h224040,24'h226464,0);
 compare_case(1,1,24'h226464,24'h246464,0);
 compare_case(0,1,24'h226464,24'h226464,0);
 compare_case(1,0,24'h226464,24'h226464,0);
 @(negedge clk);reset=1;
 @(posedge clk);#1;
 check(!feature_valid && !person_valid && feature==0 && pixel_count==0,"reset clears outputs");
 $display("RTL_REGRESSION_PASS frames=%0d checks=%0d",frames,checks);
 $finish;
end
initial begin #30000000;$fatal(1,"Watchdog timeout");end
endmodule
