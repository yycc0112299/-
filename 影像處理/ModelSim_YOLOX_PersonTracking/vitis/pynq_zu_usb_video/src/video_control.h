#ifndef VIDEO_CONTROL_H
#define VIDEO_CONTROL_H

#include <stdint.h>

enum video_control_status { VIDEO_CONTROL_OK = 0, VIDEO_CONTROL_INVALID_ARGUMENT = -1 };

struct video_control_io {
    void (*write32)(uint32_t address, uint32_t value, void *context);
    void *context;
};

struct video_control_addresses {
    uint32_t dma_base;
    uint32_t frame_id_base;
    uint32_t mailbox_base;
};

struct video_bbox_pair {
    uint32_t frame_id;
    uint16_t a_x0, a_y0, a_x1, a_y1;
    uint16_t b_x0, b_y0, b_x1, b_y1;
};

int video_control_validate(const struct video_control_io *io, const struct video_control_addresses *addresses);
int video_control_submit_pair(const struct video_control_io *io, const struct video_control_addresses *addresses, const struct video_bbox_pair *pair);

#endif
