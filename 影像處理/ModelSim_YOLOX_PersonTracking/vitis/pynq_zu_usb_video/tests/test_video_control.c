#include <assert.h>
#include <stdint.h>
#include <stdio.h>

#include "../src/video_control.h"

struct write_log { uint32_t address[8]; uint32_t value[8]; unsigned count; };
static struct write_log writes;

static void write32(uint32_t address, uint32_t value, void *context) {
    struct write_log *log = context;
    log->address[log->count] = address;
    log->value[log->count++] = value;
}

static void test_submit_writes_frame_then_payload_then_commit(void) {
    const struct video_control_io io = { .write32 = write32, .context = &writes };
    const struct video_control_addresses addresses = { .dma_base = 0xa0000000u, .frame_id_base = 0xa0010000u, .mailbox_base = 0xa0020000u };
    const struct video_bbox_pair pair = { .frame_id = 7, .a_x0 = 1, .a_y0 = 2, .a_x1 = 30, .a_y1 = 40, .b_x0 = 3, .b_y0 = 4, .b_x1 = 50, .b_y1 = 60 };
    writes.count = 0;
    assert(video_control_submit_pair(&io, &addresses, &pair) == VIDEO_CONTROL_OK);
    assert(writes.count == 7);
    assert(writes.address[0] == 0xa0010000u && writes.value[0] == 7);
    assert(writes.address[1] == 0xa0020004u && writes.value[1] == 7);
    assert(writes.address[6] == 0xa0020000u && writes.value[6] == 3);
}

static void test_rejects_missing_required_address(void) {
    const struct video_control_io io = { .write32 = write32, .context = &writes };
    const struct video_control_addresses bad = { .dma_base = 0, .frame_id_base = 0xa0010000u, .mailbox_base = 0xa0020000u };
    assert(video_control_validate(&io, &bad) == VIDEO_CONTROL_INVALID_ARGUMENT);
}

int main(void) {
    test_submit_writes_frame_then_payload_then_commit();
    test_rejects_missing_required_address();
    puts("VIDEO_CONTROL_TEST_PASS");
    return 0;
}
