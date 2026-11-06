/* Vitis standalone control entry point for pynq_zu_usb_video.xsa.
 *
 * Import the generated XSA into a Vitis platform first.  xparameters.h then
 * supplies the assigned AXI addresses; do not substitute fixed literals here.
 * UVC capture needs an application-selected USB host/UVC middleware layer.
 * Once it supplies a DDR buffer containing packed 64-bit A/B RGB words, start
 * the generated AXI DMA driver, then submit the matching bbox pair below.
 */
#include "xil_io.h"
#include "xparameters.h"
#include "video_control.h"

#ifndef XPAR_FRAME_ID_GPIO_0_BASEADDR
#error "The Vitis platform must be generated from pynq_zu_usb_video.xsa"
#endif
#ifndef XPAR_YOLOX_VIDEO_RTL_0_BASEADDR
#error "The Vitis platform must expose the RTL AXI-Lite mailbox"
#endif
#ifndef XPAR_AXI_DMA_0_BASEADDR
#error "The Vitis platform must expose the AXI DMA"
#endif

static void vitis_write32(uint32_t address, uint32_t value, void *context) {
    (void)context;
    Xil_Out32(address, value);
}

/* Retained in the ELF so JTAG can inspect the actual PS->PL smoke-test result. */
volatile uint32_t video_control_result = 0xffffffffu;
volatile uint32_t video_control_gpio_readback = 0xffffffffu;
volatile uint32_t video_control_mailbox_frame_readback = 0xffffffffu;
volatile uint32_t video_control_mailbox_status_readback = 0xffffffffu;

int main(void) {
    const struct video_control_io io = { .write32 = vitis_write32, .context = 0 };
    const struct video_control_addresses addresses = {
        .dma_base = XPAR_AXI_DMA_0_BASEADDR,
        .frame_id_base = XPAR_FRAME_ID_GPIO_0_BASEADDR,
        .mailbox_base = XPAR_YOLOX_VIDEO_RTL_0_BASEADDR,
    };
    const struct video_bbox_pair pair = {
        .frame_id = 42u,
        .a_x0 = 1u, .a_y0 = 2u, .a_x1 = 30u, .a_y1 = 40u,
        .b_x0 = 3u, .b_y0 = 4u, .b_x1 = 50u, .b_y1 = 60u,
    };
    int status = video_control_submit_pair(&io, &addresses, &pair);

    video_control_gpio_readback = Xil_In32(addresses.frame_id_base);
    video_control_mailbox_frame_readback = Xil_In32(addresses.mailbox_base + 0x04u);
    video_control_mailbox_status_readback = Xil_In32(addresses.mailbox_base);
    video_control_result = (status == VIDEO_CONTROL_OK &&
        video_control_gpio_readback == pair.frame_id &&
        video_control_mailbox_frame_readback == pair.frame_id) ? 0u : 1u;

    /* Keep the results available for JTAG inspection. */
    for (;;) { }
}
