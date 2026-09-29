`timescale 1ns/1ps
module tb_two_camera;
    reg clk=0, reset=1, frame_valid=0;
    reg [31:0] frame_id=0;
    reg [1535:0] image_a=0,image_b=0;
    reg [63:0] mask_a=0,mask_b=0;
    reg detected_a=0,detected_b=0;
    wire result_valid,valid_a,valid_b,same_person;
    wire [31:0] result_frame_id;
    wire [23:0] feature_a,feature_b;
    integer i, tests=0;
    reg [23:0] saved;
    two_camera_top dut(clk,reset,frame_valid,frame_id,image_a,image_b,
        mask_a,mask_b,detected_a,detected_b,result_valid,result_frame_id,
        valid_a,valid_b,feature_a,feature_b,same_person);
    always #5 clk=~clk;
    task fill;
        input [23:0] at,ab,bt,bb;
        begin
            for(i=0;i<64;i=i+1) begin
                image_a[i*24 +:24]=(i<32)?at:ab;
                image_b[i*24 +:24]=(i<32)?bt:bb;
            end
            mask_a=64'hffffffffffffffff; mask_b=mask_a;
            detected_a=1; detected_b=1;
        end
    endtask
    task check_frame;
        input expected_same,expected_a,expected_b;
        input [23:0] expected_fa,expected_fb;
        begin
            frame_valid=1; frame_id=frame_id+1;
            @(posedge clk); #1;
            if(result_valid!==1 || result_frame_id!==frame_id ||
               same_person!==expected_same || valid_a!==expected_a ||
               valid_b!==expected_b || feature_a!==expected_fa ||
               feature_b!==expected_fb) begin
                $display("FAIL frame=%0d same=%b valid=%b%b fa=%h fb=%h",
                    frame_id,same_person,valid_a,valid_b,feature_a,feature_b);
                $fatal(1,"frame mismatch");
            end
            tests=tests+1;
            $display("PASS frame=%0d same=%b fa=%h fb=%h",frame_id,same_person,feature_a,feature_b);
            @(negedge clk);
        end
    endtask
    initial begin
        @(posedge clk); #1;
        if(result_valid!==0 || feature_a!==0 || same_person!==0)
            $fatal(1,"reset failed");
        @(negedge clk); reset=0;
        // Similar colors across cameras and consecutive video frames.
        fill(24'h2850d2,24'hbe2828,24'h2d55d7,24'hc32d2d);
        check_frame(1,1,1,24'h426464,24'h426464);
        check_frame(1,1,1,24'h426464,24'h426464);
        fill(24'h2850d2,24'hbe2828,24'h28b93c,24'hdcdcd7);
        check_frame(0,1,1,24'h426464,24'h316464);
        // Black clothes count as foreground when included by the mask.
        fill(24'h000000,24'h000000,24'h101010,24'h101010);
        check_frame(1,1,1,24'h006464,24'h006464);
        // Detection is authoritative, even for colorful non-person input.
        detected_b=0;
        check_frame(0,1,0,24'h006464,0);
        detected_b=1; mask_b=0;
        check_frame(0,1,0,24'h006464,0);
        mask_b=64'h00000000ffffffff;
        check_frame(0,1,0,24'h006464,0);
        // Light gray folds into white; yellow is a distinct class.
        fill(24'hc8c8c8,24'hdcdc14,24'hffffff,24'he6d214);
        check_frame(1,1,1,24'h156464,24'h156464);
        fill(24'h2850d2,24'hbe2828,24'h2850d2,24'hbe2828);
        // 12/32 green: blue fraction 62%, outside 35-point tolerance.
        for(i=0;i<12;i=i+1) image_b[i*24 +:24]=24'h28b93c;
        check_frame(0,1,1,24'h426464,24'h423e64);
        // 11/32 green: blue fraction 65%, exactly on tolerance.
        image_b[11*24 +:24]=24'h2850d2;
        check_frame(1,1,1,24'h426464,24'h424164);
        // Mask excludes background regardless of its color.
        mask_b[10:0]=0;
        check_frame(1,1,1,24'h426464,24'h426464);
        saved=feature_a; frame_valid=0; image_a=0;
        @(posedge clk); #1;
        if(result_valid!==0 || feature_a!==saved)
            $fatal(1,"idle cycle must retain feature without valid result");
        @(negedge clk); reset=1;
        @(posedge clk); #1;
        if(result_valid!==0 || feature_a!==0 || feature_b!==0 || same_person!==0)
            $fatal(1,"reset must clear stored state");
        $display("ALL PASS: %0d frame cases plus idle and reset",tests);
        $finish;
    end
    initial begin #10000; $fatal(1,"timeout"); end
endmodule
