module status_display(input [1:0] status,output reg [3:0] r,g,b);
 always @* begin r=4'hf;g=4'hf;b=0;if(status==1)begin r=4'hf;g=4'h8;b=0;end else if(status==2)begin r=0;g=4'hf;b=0;end end
endmodule
