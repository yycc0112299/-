`timescale 1ns/1ps
// AXI4-Lite command mailbox for the CPU/YOLOX -> RTL boundary.
// Write the six data registers first and write CONTROL.bit0=1 last to commit
// one complete A/B detection pair.  The datapath clears the pending command
// with command_accept on the matching video frame boundary.
module yolox_bbox_axilite #(
 parameter ADDR_WIDTH = 6
)(
 input wire s_axi_aclk, input wire s_axi_aresetn,
 input wire [ADDR_WIDTH-1:0] s_axi_awaddr, input wire s_axi_awvalid, output reg s_axi_awready,
 input wire [31:0] s_axi_wdata, input wire [3:0] s_axi_wstrb, input wire s_axi_wvalid, output reg s_axi_wready,
 output reg [1:0] s_axi_bresp, output reg s_axi_bvalid, input wire s_axi_bready,
 input wire [ADDR_WIDTH-1:0] s_axi_araddr, input wire s_axi_arvalid, output reg s_axi_arready,
 output reg [31:0] s_axi_rdata, output reg [1:0] s_axi_rresp, output reg s_axi_rvalid, input wire s_axi_rready,
 output wire command_valid, output wire command_pair_present, output wire [31:0] command_frame_id,
 output wire [9:0] a_x0, a_y0, a_x1, a_y1, b_x0, b_y0, b_x1, b_y1,
 input wire command_accept, output reg overrun,
 input wire result_event, input wire confirmed_event, input wire missing_event,
 output wire irq
);
 reg pending, pair_present;
 reg [31:0] frame_id;
 reg [9:0] ax0, ay0, ax1, ay1, bx0, by0, bx1, by1;
 reg [3:0] irq_status, irq_enable;
 reg [ADDR_WIDTH-1:0] write_addr, read_addr;
 reg write_address_seen, write_data_seen;
 reg [31:0] write_data;
 reg [3:0] write_strobe;
 integer lane;

 assign command_valid = pending;
 assign command_pair_present = pair_present;
 assign command_frame_id = frame_id;
 assign a_x0=ax0; assign a_y0=ay0; assign a_x1=ax1; assign a_y1=ay1;
 assign b_x0=bx0; assign b_y0=by0; assign b_x1=bx1; assign b_y1=by1;
 // IRQ_STATUS (0x18) is write-one-to-clear; IRQ_ENABLE (0x1c) masks sources.
 // bit0=result frame, bit1=confirmed candidate, bit2=missing command, bit3=overrun.
 assign irq = |(irq_status & irq_enable);

 task apply_write;
  input [ADDR_WIDTH-1:0] addr;
  input [31:0] data;
  input [3:0] strobe;
  reg [31:0] merged;
  begin
   merged = data;
   // All command registers are documented as full 32-bit writes.  Strobes
   // are still honoured, making CPU byte writes deterministic.
   case (addr[5:2])
    4'h0: if (strobe[0] && data[0]) begin
      if (pending) overrun <= 1'b1;
      else begin pending <= 1'b1; pair_present <= data[1]; end
    end
    4'h1: begin for(lane=0;lane<4;lane=lane+1) if(strobe[lane]) frame_id[lane*8 +: 8] <= data[lane*8 +: 8]; end
    4'h2: begin
      if(strobe[0]) ax0 <= data[9:0]; if(strobe[2] || strobe[3]) ax1 <= data[25:16];
    end
    4'h3: begin
      if(strobe[0]) ay0 <= data[9:0]; if(strobe[2] || strobe[3]) ay1 <= data[25:16];
    end
    4'h4: begin
      if(strobe[0]) bx0 <= data[9:0]; if(strobe[2] || strobe[3]) bx1 <= data[25:16];
    end
    4'h5: begin
      if(strobe[0]) by0 <= data[9:0]; if(strobe[2] || strobe[3]) by1 <= data[25:16];
    end
    4'h6: begin
      if (strobe[0]) irq_status <= irq_status & ~data[3:0];
      if (strobe[0] && data[3]) overrun <= 1'b0;
    end
    4'h7: if(strobe[0]) irq_enable <= data[3:0];
   endcase
  end
 endtask

 always @(posedge s_axi_aclk) begin
  if (!s_axi_aresetn) begin
   s_axi_awready<=0; s_axi_wready<=0; s_axi_bvalid<=0; s_axi_bresp<=0;
   s_axi_arready<=0; s_axi_rvalid<=0; s_axi_rresp<=0; s_axi_rdata<=0;
   write_address_seen<=0; write_data_seen<=0; pending<=0; pair_present<=0; irq_status<=0; irq_enable<=0;
   frame_id<=0; ax0<=0; ay0<=0; ax1<=0; ay1<=0; bx0<=0; by0<=0; bx1<=0; by1<=0; overrun<=0;
  end else begin
   s_axi_awready <= !write_address_seen && !s_axi_bvalid;
   s_axi_wready <= !write_data_seen && !s_axi_bvalid;
   if (s_axi_awvalid && s_axi_awready) begin write_addr<=s_axi_awaddr; write_address_seen<=1; end
   if (s_axi_wvalid && s_axi_wready) begin write_data<=s_axi_wdata; write_strobe<=s_axi_wstrb; write_data_seen<=1; end
   if (write_address_seen && write_data_seen && !s_axi_bvalid) begin
    apply_write(write_addr,write_data,write_strobe);
    if (write_addr[5:2]==4'h0 && write_strobe[0] && write_data[0] && pending) irq_status[3] <= 1'b1;
    write_address_seen<=0; write_data_seen<=0; s_axi_bvalid<=1; s_axi_bresp<=2'b00;
   end
   if (s_axi_bvalid && s_axi_bready) s_axi_bvalid<=0;
   if (command_accept) pending<=0;
   if (result_event) irq_status[0] <= 1'b1;
   if (confirmed_event) irq_status[1] <= 1'b1;
   if (missing_event) irq_status[2] <= 1'b1;

   s_axi_arready <= !s_axi_rvalid;
   if (s_axi_arvalid && s_axi_arready) begin
    read_addr <= s_axi_araddr; s_axi_rvalid<=1; s_axi_rresp<=2'b00;
    case(s_axi_araddr[5:2])
     4'h0: s_axi_rdata <= {29'd0,overrun,pair_present,pending};
     4'h1: s_axi_rdata <= frame_id;
     4'h2: s_axi_rdata <= {6'd0,ax1,6'd0,ax0};
     4'h3: s_axi_rdata <= {6'd0,ay1,6'd0,ay0};
     4'h4: s_axi_rdata <= {6'd0,bx1,6'd0,bx0};
     4'h5: s_axi_rdata <= {6'd0,by1,6'd0,by0};
     4'h6: s_axi_rdata <= {28'd0,irq_status};
     4'h7: s_axi_rdata <= {28'd0,irq_enable};
     default: s_axi_rdata <= 0;
    endcase
   end
   if (s_axi_rvalid && s_axi_rready) s_axi_rvalid<=0;
  end
 end
endmodule
