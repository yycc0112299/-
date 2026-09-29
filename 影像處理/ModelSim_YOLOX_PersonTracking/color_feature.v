`timescale 1ns/1ps
// A cropped person ROI, row-major, pixel zero in the least significant bits.
// mask comes from an upstream person detector/segmenter, not pixel brightness.
module color_feature #(parameter W=8, H=8)(
    input [W*H*24-1:0] image_rgb,
    input [W*H-1:0] person_mask,
    input person_detected,
    output reg valid,
    output reg [23:0] feature
);
    integer upper[0:7];
    integer lower[0:7];
    integer i, c, nt, nb, ct, cb, mt, mb;
    reg [7:0] pt, pb;
    // 0 black, 1 white/light gray, 2 red, 3 green, 4 blue,
    // 5 yellow, 6 brown/orange, 7 other (including dark gray).
    function integer color8;
        input [23:0] pixel;
        integer r,g,b,mx,mn;
        begin
            r=pixel[23:16]; g=pixel[15:8]; b=pixel[7:0];
            mx=r; if(g>mx) mx=g; if(b>mx) mx=b;
            mn=r; if(g<mn) mn=g; if(b<mn) mn=b;
            if(mx<35) color8=0;
            else if(mx>=170 && mx-mn<45) color8=1;
            else if(r>140 && g>120 && b<90) color8=5;
            else if(r>g && g>b && r>80 && g-b>20) color8=6;
            else if(r>g+35 && r>b+35) color8=2;
            else if(g>r+30 && g>b+30) color8=3;
            else if(b>r+30 && b>g+30) color8=4;
            else color8=7;
        end
    endfunction
    always @* begin
        for(i=0;i<8;i=i+1) begin upper[i]=0; lower[i]=0; end
        nt=0; nb=0;
        for(i=0;i<W*H;i=i+1) begin
            c=color8(image_rgb[i*24 +: 24]);
            if(person_mask[i]) begin
                if(i<W*(H/2)) begin upper[c]=upper[c]+1; nt=nt+1; end
                else begin lower[c]=lower[c]+1; nb=nb+1; end
            end
        end
        ct=0; cb=0; mt=upper[0]; mb=lower[0];
        // Equal counts choose the smaller class number deterministically.
        for(i=1;i<8;i=i+1) begin
            if(upper[i]>mt) begin mt=upper[i]; ct=i; end
            if(lower[i]>mb) begin mb=lower[i]; cb=i; end
        end
        pt=0; pb=0;
        if(nt>0) pt=(mt*100)/nt;
        if(nb>0) pb=(mb*100)/nb;
        valid=person_detected && nt>0 && nb>0;
        feature=0;
        if(valid) feature={ct[3:0],cb[3:0],pt,pb};
    end
endmodule
