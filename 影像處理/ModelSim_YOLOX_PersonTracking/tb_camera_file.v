`timescale 1ns/1ps
module tb_camera_file;
 parameter FRAME_COUNT=90;
 localparam W=640,H=480,N=W*H;
 reg clk=0,reset=1,pixel_valid=0,frame_start=0;
 reg [23:0] pixel_rgb=0;
 wire feature_valid;
 wire [23:0] feature;
 wire [31:0] pixel_count;
 reg [23:0] previous_feature;
 reg [7:0] frame_bytes[0:N*3-1];
 integer f,p,source,outfile,count;
 reg color_similar;
 color_feature_stream #(W,H) dut(clk,reset,pixel_valid,frame_start,pixel_rgb,feature_valid,feature,pixel_count);
 always #5 clk=~clk;
 function integer diff;
 input [7:0] a,b;
 begin if(a>=b)diff=a-b;else diff=b-a;end
 endfunction
 initial begin
 source=$fopen("pixels.rgb","rb");outfile=$fopen("comparison.csv","w");
 if(!source || !outfile || FRAME_COUNT<2)$fatal(1,"Invalid input or output");
 $fdisplay(outfile,"frame_a,frame_b,feature_a,feature_b,color_similar");
 @(negedge clk);reset=0;
 for(f=0;f<FRAME_COUNT;f=f+1)begin
 count=$fread(frame_bytes,source);
 if(count!=N*3)$fatal(1,"Incomplete frame %0d: %0d bytes",f,count);
 for(p=0;p<N;p=p+1)begin
 pixel_rgb={frame_bytes[p*3],frame_bytes[p*3+1],frame_bytes[p*3+2]};
 pixel_valid=1;frame_start=(p==0);
 @(posedge clk);#1;
 if(p<N-1 && feature_valid!==0)$fatal(1,"Premature feature");
 @(negedge clk);
 end
 if(feature_valid!==1 || pixel_count!==N || (^feature)===1'bx)$fatal(1,"Invalid full-resolution result at frame %0d",f);
 if(f>0)begin
 color_similar=previous_feature[23:16]==feature[23:16]
 && diff(previous_feature[15:8],feature[15:8])<=35
 && diff(previous_feature[7:0],feature[7:0])<=35;
 $fdisplay(outfile,"%0d,%0d,%06h,%06h,%0d",f-1,f,previous_feature,feature,color_similar);
 end
 previous_feature=feature;
 $display("FRAME %0d: %0d pixels feature=%06h",f,pixel_count,feature);
 pixel_valid=0;frame_start=0;
 @(posedge clk);#1;
 if(feature_valid!==0)$fatal(1,"feature_valid did not clear");
 @(negedge clk);
 end
 if($fgetc(source)!=-1)$fatal(1,"Unexpected trailing image data");
 $fclose(source);$fclose(outfile);
 $display("CAMERA_RUN_PASS: %0d adjacent pairs, 640x480, %0d pixels/frame",FRAME_COUNT-1,N);
 $finish;
 end
endmodule
