/*
 * Linux-side source half of the PYNQ-ZU UVC -> DDR -> PL pipeline.
 *
 * This is intended to be built by Vitis' AArch64 Linux toolchain, not the
 * standalone BSP.  It uses the kernel UVC/V4L2 driver for two YUYV cameras,
 * converts one synchronously dequeued frame from each to the exact 64-bit
 * A/B RGB word contract consumed by dual_camera_yolox_axis_top.
 *
 * For safe bring-up the packed words are written to a regular output file.
 * Production DMA needs a board-provided contiguous DMA buffer (dma-heap,
 * udmabuf, or a driver allocation); its physical address must then be passed
 * to the tested AXI-DMA controller rather than treating malloc/file memory as
 * DMA-safe.
 */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <linux/videodev2.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>

enum { WIDTH = 640, HEIGHT = 480, PIXELS = WIDTH * HEIGHT };

struct camera {
    int fd;
    void *buffers[3];
    size_t lengths[3];
    unsigned int count;
};

static int xioctl(int fd, unsigned long request, void *arg) {
    int rc;
    do { rc = ioctl(fd, request, arg); } while (rc < 0 && errno == EINTR);
    return rc;
}

static int start_camera(struct camera *camera, const char *path) {
    struct v4l2_capability capability;
    struct v4l2_format format;
    struct v4l2_requestbuffers request;
    memset(camera, 0, sizeof(*camera));
    camera->fd = open(path, O_RDWR | O_CLOEXEC);
    if (camera->fd < 0) return -1;
    memset(&capability, 0, sizeof(capability));
    if (xioctl(camera->fd, VIDIOC_QUERYCAP, &capability) < 0 ||
        !(capability.capabilities & V4L2_CAP_VIDEO_CAPTURE) ||
        !(capability.capabilities & V4L2_CAP_STREAMING)) return -1;
    memset(&format, 0, sizeof(format));
    format.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    format.fmt.pix.width = WIDTH;
    format.fmt.pix.height = HEIGHT;
    format.fmt.pix.pixelformat = V4L2_PIX_FMT_YUYV;
    format.fmt.pix.field = V4L2_FIELD_NONE;
    if (xioctl(camera->fd, VIDIOC_S_FMT, &format) < 0 ||
        format.fmt.pix.width != WIDTH || format.fmt.pix.height != HEIGHT ||
        format.fmt.pix.pixelformat != V4L2_PIX_FMT_YUYV) return -1;
    memset(&request, 0, sizeof(request));
    request.count = 3;
    request.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    request.memory = V4L2_MEMORY_MMAP;
    if (xioctl(camera->fd, VIDIOC_REQBUFS, &request) < 0 || request.count < 2) return -1;
    camera->count = request.count;
    for (unsigned int i = 0; i < camera->count; ++i) {
        struct v4l2_buffer buffer;
        memset(&buffer, 0, sizeof(buffer));
        buffer.type = request.type; buffer.memory = request.memory; buffer.index = i;
        if (xioctl(camera->fd, VIDIOC_QUERYBUF, &buffer) < 0) return -1;
        camera->lengths[i] = buffer.length;
        camera->buffers[i] = mmap(NULL, buffer.length, PROT_READ | PROT_WRITE,
                                  MAP_SHARED, camera->fd, buffer.m.offset);
        if (camera->buffers[i] == MAP_FAILED) return -1;
        if (xioctl(camera->fd, VIDIOC_QBUF, &buffer) < 0) return -1;
    }
    enum v4l2_buf_type type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    return xioctl(camera->fd, VIDIOC_STREAMON, &type);
}

static int dequeue_frame(struct camera *camera, struct v4l2_buffer *buffer) {
    memset(buffer, 0, sizeof(*buffer));
    buffer->type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    buffer->memory = V4L2_MEMORY_MMAP;
    return xioctl(camera->fd, VIDIOC_DQBUF, buffer);
}

static uint8_t clip_u8(int value) { return (uint8_t)(value < 0 ? 0 : value > 255 ? 255 : value); }
static void yuv_to_rgb(uint8_t y, uint8_t u, uint8_t v, uint8_t *r, uint8_t *g, uint8_t *b) {
    int c = (int)y - 16, d = (int)u - 128, e = (int)v - 128;
    *r = clip_u8((298 * c + 409 * e + 128) >> 8);
    *g = clip_u8((298 * c - 100 * d - 208 * e + 128) >> 8);
    *b = clip_u8((298 * c + 516 * d + 128) >> 8);
}
static uint32_t yuyv_rgb24(const uint8_t *source, unsigned int pixel) {
    const uint8_t *p = source + (pixel & ~1u) * 2u;
    uint8_t r, g, b; yuv_to_rgb(p[(pixel & 1u) ? 2 : 0], p[1], p[3], &r, &g, &b);
    return ((uint32_t)r << 16) | ((uint32_t)g << 8) | b;
}
static void pack_dual_yuyv(const uint8_t *a, const uint8_t *b, uint64_t *output) {
    for (unsigned int pixel = 0; pixel < PIXELS; ++pixel)
        output[pixel] = (uint64_t)yuyv_rgb24(a, pixel) | ((uint64_t)yuyv_rgb24(b, pixel) << 32);
}

static void close_camera(struct camera *camera) {
    if (camera->fd < 0) return;
    enum v4l2_buf_type type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    (void)xioctl(camera->fd, VIDIOC_STREAMOFF, &type);
    for (unsigned int i = 0; i < camera->count; ++i)
        if (camera->buffers[i] && camera->buffers[i] != MAP_FAILED) munmap(camera->buffers[i], camera->lengths[i]);
    close(camera->fd); camera->fd = -1;
}

int main(int argc, char **argv) {
    const char *path_a = argc > 1 ? argv[1] : "/dev/video0";
    const char *path_b = argc > 2 ? argv[2] : "/dev/video2";
    const char *output_path = argc > 3 ? argv[3] : "dual_rgb888_640x480.bin";
    struct camera a = { .fd = -1 }, b = { .fd = -1 };
    struct v4l2_buffer frame_a, frame_b;
    uint64_t *packed = NULL;
    int rc = 1;
    if (start_camera(&a, path_a) < 0 || start_camera(&b, path_b) < 0 ||
        dequeue_frame(&a, &frame_a) < 0 || dequeue_frame(&b, &frame_b) < 0 ||
        frame_a.bytesused < PIXELS * 2u || frame_b.bytesused < PIXELS * 2u) goto done;
    packed = aligned_alloc(64, PIXELS * sizeof(*packed));
    if (!packed) goto done;
    pack_dual_yuyv(a.buffers[frame_a.index], b.buffers[frame_b.index], packed);
    int output = open(output_path, O_WRONLY | O_CREAT | O_TRUNC | O_CLOEXEC, 0644);
    if (output < 0 || write(output, packed, PIXELS * sizeof(*packed)) != (ssize_t)(PIXELS * sizeof(*packed))) { if (output >= 0) close(output); goto done; }
    close(output); rc = 0;
done:
    if (rc) fprintf(stderr, "UVC capture/pack failed: %s\n", strerror(errno));
    free(packed); close_camera(&a); close_camera(&b); return rc;
}
