`timescale 1ns/1ps
module tb_person_roi;
 reg clk=0,reset=1,pixel_valid=0,frame_start=0,person_detected=0;
 reg [23:0] pixel_rgb=0;
 reg [9:0] x0=0,y0=0,x1=0,y1=0;
 wire feature_valid,person_valid;
 wire [23:0] feature;
 wire [31:0] top_pixels,bottom_pixels,pixel_count;
 reg [7:0] data[0:921599];
 integer regions,pixels,outfile,status,count,p,samples;
 integer frame_id,track_id,det,rx0,ry0,rx1,ry1;
 reg [23:0] history[0:4095];
 reg history_valid[0:4095];
 reg previous_valid=0;
 reg [23:0] previous_feature=0;
 wire color_similar;
 integer h;
 person_feature_compare compare(previous_valid,person_valid,previous_feature,feature,color_similar);
 person_roi_stream dut(clk,reset,pixel_valid,frame_start,person_detected,pixel_rgb,
 x0,y0,x1,y1,feature_valid,person_valid,feature,top_pixels,bottom_pixels,pixel_count);
 always #5 clk=~clk;
 initial begin
 regions=$fopen("regions.txt","r");pixels=$fopen("pixels.rgb","rb");outfile=$fopen("features.csv","w");
 if(!regions || !pixels || !outfile)$fatal(1,"Cannot open files");
 $fdisplay(outfile,"frame,track_id,valid,feature,top_pixels,bottom_pixels,previous_available,color_similar");
 for(h=0;h<4096;h=h+1)begin history[h]=0;history_valid[h]=0;end
 @(negedge clk);reset=0;samples=0;
 status=$fscanf(regions,"%d %d %d %d %d %d %d",frame_id,track_id,det,rx0,ry0,rx1,ry1);
 while(status==7)begin
 if(track_id<0 || track_id>4095)$fatal(1,"Track ID exceeds testbench history capacity");
 previous_valid=history_valid[track_id];previous_feature=history[track_id];
 if(rx0<0 || ry0<0 || rx1>640 || ry1>480 || rx1<rx0 || ry1<ry0)$fatal(1,"Invalid ROI");
 x0=rx0;y0=ry0;x1=rx1;y1=ry1;person_detected=det;
 status=$fseek(pixels,frame_id*921600,0);
 if(status!=0)$fatal(1,"Seek failed");
 count=$fread(data,pixels);
 if(count!=921600)$fatal(1,"Incomplete frame");
 for(p=0;p<307200;p=p+1)begin
 pixel_rgb={data[p*3],data[p*3+1],data[p*3+2]};pixel_valid=1;frame_start=(p==0);
 @(posedge clk);#1;
 if(p<307199 && feature_valid!==0)$fatal(1,"Early result");
 @(negedge clk);
 end
 if(feature_valid!==1 || pixel_count!==307200 || (^feature)===1'bx)$fatal(1,"Invalid feature");
 $fdisplay(outfile,"%0d,%0d,%0d,%06h,%0d,%0d,%0d,%0d",frame_id,track_id,person_valid,feature,top_pixels,bottom_pixels,previous_valid,color_similar);
 if(person_valid)begin history[track_id]=feature;history_valid[track_id]=1;end
 samples=samples+1;pixel_valid=0;frame_start=0;
 @(posedge clk);#1;
 if(feature_valid!==0)$fatal(1,"Result pulse did not clear");
 @(negedge clk);
 status=$fscanf(regions,"%d %d %d %d %d %d %d",frame_id,track_id,det,rx0,ry0,rx1,ry1);
 end
 if(!$feof(regions))$fatal(1,"Malformed ROI record");
 $fclose(regions);$fclose(pixels);$fclose(outfile);
 if(samples==0)$fatal(1,"No samples");
 $display("PERSON_RTL_PASS: %0d person/empty regions",samples);$finish;
 end
endmodule
