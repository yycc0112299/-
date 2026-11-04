`timescale 1ns/1ps
// PYNQ-ZU integration top: PS/YOLOX writes one selected A/B bbox pair through
// AXI4-Lite; synchronized RGB video is processed entirely in the RTL path.
// All ports use one PL clock.  Insert AMD clock converters if PS AXI/video use
// different clocks in the eventual Block Design.
module dual_camera_yolox_axilite_top #(
 parameter AXI_ADDR_WIDTH=6
)(
 (* X_INTERFACE_PARAMETER = "XIL_INTERFACENAME clk, ASSOCIATED_BUSIF S_AXI, ASSOCIATED_RESET reset:s_axi_aresetn, FREQ_HZ 100000000", X_INTERFACE_INFO = "xilinx.com:signal:clock:1.0 clk CLK" *) input wire clk,
 (* X_INTERFACE_PARAMETER = "XIL_INTERFACENAME reset, POLARITY ACTIVE_HIGH", X_INTERFACE_INFO = "xilinx.com:signal:reset:1.0 reset RST" *) input wire reset,
 input wire pixel_valid, input wire frame_start, input wire [31:0] stream_frame_id,
 input wire [23:0] pixel_rgb_a, input wire [23:0] pixel_rgb_b,
 (* X_INTERFACE_PARAMETER = "XIL_INTERFACENAME S_AXI, PROTOCOL AXI4LITE, DATA_WIDTH 32, ADDR_WIDTH 6, READ_WRITE_MODE READ_WRITE, HAS_BRESP 1, HAS_RRESP 1", X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI AWADDR" *) input wire [AXI_ADDR_WIDTH-1:0] s_axi_awaddr,
 (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI AWVALID" *) input wire s_axi_awvalid,
 (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI AWREADY" *) output wire s_axi_awready,
 (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI WDATA" *) input wire [31:0] s_axi_wdata,
 (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI WSTRB" *) input wire [3:0] s_axi_wstrb,
 (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI WVALID" *) input wire s_axi_wvalid,
 (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI WREADY" *) output wire s_axi_wready,
 (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI BRESP" *) output wire [1:0] s_axi_bresp,
 (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI BVALID" *) output wire s_axi_bvalid,
 (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI BREADY" *) input wire s_axi_bready,
 (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI ARADDR" *) input wire [AXI_ADDR_WIDTH-1:0] s_axi_araddr,
 (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI ARVALID" *) input wire s_axi_arvalid,
 (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI ARREADY" *) output wire s_axi_arready,
 (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI RDATA" *) output wire [31:0] s_axi_rdata,
 (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI RRESP" *) output wire [1:0] s_axi_rresp,
 (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI RVALID" *) output wire s_axi_rvalid,
 (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI RREADY" *) input wire s_axi_rready,
 (* X_INTERFACE_PARAMETER = "XIL_INTERFACENAME s_axi_aresetn, POLARITY ACTIVE_LOW", X_INTERFACE_INFO = "xilinx.com:signal:reset:1.0 s_axi_aresetn RST" *) input wire s_axi_aresetn,
 output wire command_overrun, output wire frame_command_missing,
 output wire feature_valid_a, feature_valid_b, person_valid_a, person_valid_b,
 output wire [23:0] feature_a, feature_b, output wire feature_similar, candidate_valid, confirmed,
 output wire [1:0] consecutive_hits
);
 wire command_valid, command_pair_present, command_accept;
 wire [31:0] command_frame_id;
 wire [9:0] ax0, ay0, ax1, ay1, bx0, by0, bx1, by1;
 wire person_detected_a, person_detected_b;
 wire [9:0] live_ax0, live_ay0, live_ax1, live_ay1, live_bx0, live_by0, live_bx1, live_by1;

 yolox_bbox_axilite #(.ADDR_WIDTH(AXI_ADDR_WIDTH)) mailbox(
  .s_axi_aclk(clk), .s_axi_aresetn(s_axi_aresetn), .s_axi_awaddr(s_axi_awaddr), .s_axi_awvalid(s_axi_awvalid), .s_axi_awready(s_axi_awready),
  .s_axi_wdata(s_axi_wdata), .s_axi_wstrb(s_axi_wstrb), .s_axi_wvalid(s_axi_wvalid), .s_axi_wready(s_axi_wready),
  .s_axi_bresp(s_axi_bresp), .s_axi_bvalid(s_axi_bvalid), .s_axi_bready(s_axi_bready), .s_axi_araddr(s_axi_araddr), .s_axi_arvalid(s_axi_arvalid), .s_axi_arready(s_axi_arready),
  .s_axi_rdata(s_axi_rdata), .s_axi_rresp(s_axi_rresp), .s_axi_rvalid(s_axi_rvalid), .s_axi_rready(s_axi_rready),
  .command_valid(command_valid), .command_pair_present(command_pair_present), .command_frame_id(command_frame_id),
  .a_x0(ax0),.a_y0(ay0),.a_x1(ax1),.a_y1(ay1),.b_x0(bx0),.b_y0(by0),.b_x1(bx1),.b_y1(by1),.command_accept(command_accept),.overrun(command_overrun));
 yolox_frame_command_adapter adapter(
  .clk(clk),.reset(reset),.frame_start(frame_start),.stream_frame_id(stream_frame_id),.command_valid(command_valid),.command_pair_present(command_pair_present),.command_frame_id(command_frame_id),
  .command_a_x0(ax0),.command_a_y0(ay0),.command_a_x1(ax1),.command_a_y1(ay1),.command_b_x0(bx0),.command_b_y0(by0),.command_b_x1(bx1),.command_b_y1(by1),
  .command_accept(command_accept),.frame_command_missing(frame_command_missing),.person_detected_a(person_detected_a),.person_detected_b(person_detected_b),
  .a_x0(live_ax0),.a_y0(live_ay0),.a_x1(live_ax1),.a_y1(live_ay1),.b_x0(live_bx0),.b_y0(live_by0),.b_x1(live_bx1),.b_y1(live_by1));
 dual_camera_roi_match_top core(
  .clk(clk),.reset(reset),.pixel_valid(pixel_valid),.frame_start(frame_start),.person_detected_a(person_detected_a),.person_detected_b(person_detected_b),
  .pixel_rgb_a(pixel_rgb_a),.pixel_rgb_b(pixel_rgb_b),.x0_a(live_ax0),.y0_a(live_ay0),.x1_a(live_ax1),.y1_a(live_ay1),.x0_b(live_bx0),.y0_b(live_by0),.x1_b(live_bx1),.y1_b(live_by1),
  .feature_valid_a(feature_valid_a),.feature_valid_b(feature_valid_b),.person_valid_a(person_valid_a),.person_valid_b(person_valid_b),.feature_a(feature_a),.feature_b(feature_b),.feature_similar(feature_similar),.candidate_valid(candidate_valid),.confirmed(confirmed),.consecutive_hits(consecutive_hits));
endmodule
