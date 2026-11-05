`timescale 1ns/1ps
// AXI-stream variant for a single DMA carrying lock-step A/B RGB pixels.
// A PYNQ program packs each pair as: B in bits 55:32, A in bits 23:0.
module dual_camera_yolox_axis_top #(
 parameter AXI_ADDR_WIDTH=6,
 parameter [31:0] FRAME_PIXELS=32'd307200
)(
 (* X_INTERFACE_PARAMETER = "XIL_INTERFACENAME clk, ASSOCIATED_BUSIF S_AXI:S_AXIS_VIDEO, ASSOCIATED_RESET reset:s_axi_aresetn, FREQ_HZ 100000000", X_INTERFACE_INFO = "xilinx.com:signal:clock:1.0 clk CLK" *) input wire clk,
 (* X_INTERFACE_PARAMETER = "XIL_INTERFACENAME reset, POLARITY ACTIVE_HIGH", X_INTERFACE_INFO = "xilinx.com:signal:reset:1.0 reset RST" *) input wire reset,
 input wire [31:0] stream_frame_id,
 (* X_INTERFACE_PARAMETER = "XIL_INTERFACENAME S_AXIS_VIDEO, TDATA_NUM_BYTES 8, HAS_TLAST 1", X_INTERFACE_INFO = "xilinx.com:interface:axis:1.0 S_AXIS_VIDEO TDATA" *) input wire [63:0] s_axis_video_tdata,
 (* X_INTERFACE_INFO = "xilinx.com:interface:axis:1.0 S_AXIS_VIDEO TVALID" *) input wire s_axis_video_tvalid,
 (* X_INTERFACE_INFO = "xilinx.com:interface:axis:1.0 S_AXIS_VIDEO TREADY" *) output wire s_axis_video_tready,
 (* X_INTERFACE_INFO = "xilinx.com:interface:axis:1.0 S_AXIS_VIDEO TLAST" *) input wire s_axis_video_tlast,
 input wire s_axi_aresetn, input wire [AXI_ADDR_WIDTH-1:0] s_axi_awaddr, input wire s_axi_awvalid, output wire s_axi_awready,
 input wire [31:0] s_axi_wdata, input wire [3:0] s_axi_wstrb, input wire s_axi_wvalid, output wire s_axi_wready,
 output wire [1:0] s_axi_bresp, output wire s_axi_bvalid, input wire s_axi_bready,
 input wire [AXI_ADDR_WIDTH-1:0] s_axi_araddr, input wire s_axi_arvalid, output wire s_axi_arready,
 output wire [31:0] s_axi_rdata, output wire [1:0] s_axi_rresp, output wire s_axi_rvalid, input wire s_axi_rready,
 output wire stream_frame_boundary_error, output wire command_overrun, output wire frame_command_missing,
 output wire feature_valid_a, feature_valid_b, person_valid_a, person_valid_b,
 output wire [23:0] feature_a, feature_b, output wire feature_similar, candidate_valid, confirmed,
 output wire [1:0] consecutive_hits, output wire irq
);
 wire pixel_valid, frame_start;
 wire [23:0] pixel_rgb_a, pixel_rgb_b;
 axis_dual_rgb_stream_adapter #(.FRAME_PIXELS(FRAME_PIXELS)) adapter(
  .clk(clk),.reset(reset),.s_axis_tdata(s_axis_video_tdata),.s_axis_tvalid(s_axis_video_tvalid),.s_axis_tready(s_axis_video_tready),.s_axis_tlast(s_axis_video_tlast),
  .pixel_valid(pixel_valid),.frame_start(frame_start),.pixel_rgb_a(pixel_rgb_a),.pixel_rgb_b(pixel_rgb_b),.frame_boundary_error(stream_frame_boundary_error));
 dual_camera_yolox_axilite_top #(.AXI_ADDR_WIDTH(AXI_ADDR_WIDTH)) core(
  .clk(clk),.reset(reset),.pixel_valid(pixel_valid),.frame_start(frame_start),.stream_frame_id(stream_frame_id),.pixel_rgb_a(pixel_rgb_a),.pixel_rgb_b(pixel_rgb_b),
  .s_axi_aresetn(s_axi_aresetn),.s_axi_awaddr(s_axi_awaddr),.s_axi_awvalid(s_axi_awvalid),.s_axi_awready(s_axi_awready),.s_axi_wdata(s_axi_wdata),.s_axi_wstrb(s_axi_wstrb),.s_axi_wvalid(s_axi_wvalid),.s_axi_wready(s_axi_wready),.s_axi_bresp(s_axi_bresp),.s_axi_bvalid(s_axi_bvalid),.s_axi_bready(s_axi_bready),.s_axi_araddr(s_axi_araddr),.s_axi_arvalid(s_axi_arvalid),.s_axi_arready(s_axi_arready),.s_axi_rdata(s_axi_rdata),.s_axi_rresp(s_axi_rresp),.s_axi_rvalid(s_axi_rvalid),.s_axi_rready(s_axi_rready),
  .command_overrun(command_overrun),.frame_command_missing(frame_command_missing),.feature_valid_a(feature_valid_a),.feature_valid_b(feature_valid_b),.person_valid_a(person_valid_a),.person_valid_b(person_valid_b),.feature_a(feature_a),.feature_b(feature_b),.feature_similar(feature_similar),.candidate_valid(candidate_valid),.confirmed(confirmed),.consecutive_hits(consecutive_hits),.irq(irq));
endmodule
