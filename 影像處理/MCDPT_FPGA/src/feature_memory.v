module feature_memory(input clk,write_en,input [63:0] data_in,output reg [63:0] data_out);
  always @(posedge clk) if(write_en)data_out<=data_in;
endmodule
