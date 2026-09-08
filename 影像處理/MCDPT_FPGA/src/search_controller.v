`include "mcdpt_defs.vh"
module search_controller(input clk,rst,init,advance,output [7:0] x,output [6:0] y,output last);
  reg [7:0] xi;reg [6:0] yi;assign x=xi;assign y=yi;assign last=(xi==`SEARCH_X_MAX)&&(yi==`SEARCH_Y_MAX);
  always @(posedge clk)begin
    if(rst||init)begin xi<=`SEARCH_X_MIN;yi<=`SEARCH_Y_MIN;end
    else if(advance)begin if(xi==`SEARCH_X_MAX)begin xi<=`SEARCH_X_MIN;if(yi<`SEARCH_Y_MAX)yi<=yi+`SEARCH_STRIDE;end else xi<=xi+`SEARCH_STRIDE;end
  end
endmodule
