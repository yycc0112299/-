#include "video_control.h"

enum { CONTROL = 0x00, FRAME_ID = 0x04, A_X = 0x08, A_Y = 0x0c, B_X = 0x10, B_Y = 0x14 };

static uint32_t packed_pair(uint16_t low, uint16_t high) {
    return ((uint32_t)(high & 0x03ffu) << 16) | (uint32_t)(low & 0x03ffu);
}

int video_control_validate(const struct video_control_io *io, const struct video_control_addresses *addresses) {
    if (!io || !io->write32 || !addresses || !addresses->dma_base || !addresses->frame_id_base || !addresses->mailbox_base)
        return VIDEO_CONTROL_INVALID_ARGUMENT;
    return VIDEO_CONTROL_OK;
}

int video_control_submit_pair(const struct video_control_io *io, const struct video_control_addresses *addresses, const struct video_bbox_pair *pair) {
    if (video_control_validate(io, addresses) != VIDEO_CONTROL_OK || !pair)
        return VIDEO_CONTROL_INVALID_ARGUMENT;
    io->write32(addresses->frame_id_base, pair->frame_id, io->context);
    io->write32(addresses->mailbox_base + FRAME_ID, pair->frame_id, io->context);
    io->write32(addresses->mailbox_base + A_X, packed_pair(pair->a_x0, pair->a_x1), io->context);
    io->write32(addresses->mailbox_base + A_Y, packed_pair(pair->a_y0, pair->a_y1), io->context);
    io->write32(addresses->mailbox_base + B_X, packed_pair(pair->b_x0, pair->b_x1), io->context);
    io->write32(addresses->mailbox_base + B_Y, packed_pair(pair->b_y0, pair->b_y1), io->context);
    io->write32(addresses->mailbox_base + CONTROL, 0x3u, io->context);
    return VIDEO_CONTROL_OK;
}
