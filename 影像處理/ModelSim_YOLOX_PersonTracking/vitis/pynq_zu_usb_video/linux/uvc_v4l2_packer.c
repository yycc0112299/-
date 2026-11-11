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
#include <stdbool.h>
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

/* The PL/DMA contract is always two 640x480 RGB frames.  C270s sharing the
 * PYNQ-ZU's USB2 hub cannot reserve two VGA YUYV isochronous streams, even at
 * a requested 10 FPS. Capture a lower-bandwidth QVGA source and upscale each
 * pixel 2x2 while retaining the established DMA word count. This is a
 * diagnostic fallback, not a proof that the shared hub can run both cameras. */
enum {
    WIDTH = 640, HEIGHT = 480, PIXELS = WIDTH * HEIGHT,
    CAPTURE_WIDTH = 320, CAPTURE_HEIGHT = 240, TARGET_FPS = 10
};

struct camera {
    int fd;
    void *buffers[3];
    size_t lengths[3];
    unsigned int count;
};

static uint32_t requested_pixelformat = V4L2_PIX_FMT_YUYV;

static int xioctl(int fd, unsigned long request, void *arg) {
    int rc;
    do { rc = ioctl(fd, request, arg); } while (rc < 0 && errno == EINTR);
    return rc;
}

static void fourcc_text(uint32_t fourcc, char text[5]) {
    text[0] = (char)(fourcc & 0xffu); text[1] = (char)((fourcc >> 8) & 0xffu);
    text[2] = (char)((fourcc >> 16) & 0xffu); text[3] = (char)((fourcc >> 24) & 0xffu);
    text[4] = '\0';
}

/* A board-side capability report avoids relying on desktop-only v4l2-ctl when
 * selecting a two-camera format for this exact USB topology. */
static int probe_camera(const char *path) {
    int fd = open(path, O_RDWR | O_CLOEXEC);
    if (fd < 0) { perror(path); return 1; }
    for (unsigned int fi = 0;; ++fi) {
        struct v4l2_fmtdesc format;
        memset(&format, 0, sizeof(format));
        format.type = V4L2_BUF_TYPE_VIDEO_CAPTURE; format.index = fi;
        if (xioctl(fd, VIDIOC_ENUM_FMT, &format) < 0) break;
        char name[5]; fourcc_text(format.pixelformat, name);
        printf("format=%s description=%s\n", name, format.description);
        for (unsigned int si = 0;; ++si) {
            struct v4l2_frmsizeenum size;
            memset(&size, 0, sizeof(size)); size.index = si; size.pixel_format = format.pixelformat;
            if (xioctl(fd, VIDIOC_ENUM_FRAMESIZES, &size) < 0) break;
            if (size.type != V4L2_FRMSIZE_TYPE_DISCRETE) continue;
            printf("  size=%ux%u", size.discrete.width, size.discrete.height);
            for (unsigned int ii = 0;; ++ii) {
                struct v4l2_frmivalenum interval;
                memset(&interval, 0, sizeof(interval)); interval.index = ii;
                interval.pixel_format = format.pixelformat;
                interval.width = size.discrete.width; interval.height = size.discrete.height;
                if (xioctl(fd, VIDIOC_ENUM_FRAMEINTERVALS, &interval) < 0) break;
                if (interval.type == V4L2_FRMIVAL_TYPE_DISCRETE && interval.discrete.numerator)
                    printf(" %u/%u-fps", interval.discrete.denominator, interval.discrete.numerator);
            }
            putchar('\n');
        }
    }
    close(fd); return 0;
}

static int start_camera(struct camera *camera, const char *path) {
    struct v4l2_capability capability;
    struct v4l2_format format;
    struct v4l2_requestbuffers request;
    memset(camera, 0, sizeof(*camera));
    camera->fd = open(path, O_RDWR | O_CLOEXEC);
    if (camera->fd < 0) { perror(path); return -1; }
    memset(&capability, 0, sizeof(capability));
    if (xioctl(camera->fd, VIDIOC_QUERYCAP, &capability) < 0 ||
        !(capability.capabilities & V4L2_CAP_VIDEO_CAPTURE) ||
        !(capability.capabilities & V4L2_CAP_STREAMING)) {
        perror("VIDIOC_QUERYCAP"); return -1;
    }
    memset(&format, 0, sizeof(format));
    format.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    format.fmt.pix.width = CAPTURE_WIDTH;
    format.fmt.pix.height = CAPTURE_HEIGHT;
    format.fmt.pix.pixelformat = requested_pixelformat;
    format.fmt.pix.field = V4L2_FIELD_NONE;
    if (xioctl(camera->fd, VIDIOC_S_FMT, &format) < 0 ||
        format.fmt.pix.width != CAPTURE_WIDTH || format.fmt.pix.height != CAPTURE_HEIGHT ||
        format.fmt.pix.pixelformat != requested_pixelformat) {
        perror("VIDIOC_S_FMT"); return -1;
    }
    /* Two C270s share the board's USB2 hub. Do not accept the driver's
       high-FPS default: request an explicitly modest source rate. */
    struct v4l2_streamparm stream;
    memset(&stream, 0, sizeof(stream));
    stream.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    stream.parm.capture.timeperframe.numerator = 1;
    stream.parm.capture.timeperframe.denominator = TARGET_FPS;
    if (xioctl(camera->fd, VIDIOC_S_PARM, &stream) < 0) { perror("VIDIOC_S_PARM"); return -1; }
    if (stream.parm.capture.timeperframe.numerator) {
        char format_name[5]; fourcc_text(requested_pixelformat, format_name);
        fprintf(stderr, "%s: negotiated %u/%u FPS at %ux%u %s\n", path,
                stream.parm.capture.timeperframe.denominator,
                stream.parm.capture.timeperframe.numerator,
                CAPTURE_WIDTH, CAPTURE_HEIGHT, format_name);
    }
    memset(&request, 0, sizeof(request));
    request.count = 3;
    request.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    request.memory = V4L2_MEMORY_MMAP;
    if (xioctl(camera->fd, VIDIOC_REQBUFS, &request) < 0 || request.count < 2) { perror("VIDIOC_REQBUFS"); return -1; }
    camera->count = request.count;
    for (unsigned int i = 0; i < camera->count; ++i) {
        struct v4l2_buffer buffer;
        memset(&buffer, 0, sizeof(buffer));
        buffer.type = request.type; buffer.memory = request.memory; buffer.index = i;
        if (xioctl(camera->fd, VIDIOC_QUERYBUF, &buffer) < 0) { perror("VIDIOC_QUERYBUF"); return -1; }
        camera->lengths[i] = buffer.length;
        camera->buffers[i] = mmap(NULL, buffer.length, PROT_READ | PROT_WRITE,
                                  MAP_SHARED, camera->fd, buffer.m.offset);
        if (camera->buffers[i] == MAP_FAILED) { perror("mmap"); return -1; }
        if (xioctl(camera->fd, VIDIOC_QBUF, &buffer) < 0) { perror("VIDIOC_QBUF"); return -1; }
    }
    enum v4l2_buf_type type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    if (xioctl(camera->fd, VIDIOC_STREAMON, &type) < 0) {
        fprintf(stderr, "%s: VIDIOC_STREAMON: %s\n", path, strerror(errno));
        return -1;
    }
    return 0;
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
    for (unsigned int y = 0; y < HEIGHT; ++y) {
        for (unsigned int x = 0; x < WIDTH; ++x) {
            unsigned int source_pixel = (y / 2u) * CAPTURE_WIDTH + (x / 2u);
            unsigned int output_pixel = y * WIDTH + x;
            output[output_pixel] = (uint64_t)yuyv_rgb24(a, source_pixel) |
                ((uint64_t)yuyv_rgb24(b, source_pixel) << 32);
        }
    }
}

/* The deployed topology is one C270 per PYNQ-ZU.  Keep the same AXI-stream
 * word contract as the two-lane RTL, but explicitly black-fill the lane that
 * belongs to the other board rather than duplicating a camera and pretending
 * there are two independent sources. */
static void pack_single_yuyv_lane(const uint8_t *source, bool source_is_b, uint64_t *output) {
    for (unsigned int y = 0; y < HEIGHT; ++y) {
        for (unsigned int x = 0; x < WIDTH; ++x) {
            unsigned int source_pixel = (y / 2u) * CAPTURE_WIDTH + (x / 2u);
            unsigned int output_pixel = y * WIDTH + x;
            uint64_t rgb = yuyv_rgb24(source, source_pixel);
            output[output_pixel] = source_is_b ? (rgb << 32) : rgb;
        }
    }
}

static void close_camera(struct camera *camera);

static int write_packed_frame(const char *output_path, const uint64_t *packed) {
    int output = open(output_path, O_WRONLY | O_CREAT | O_TRUNC | O_CLOEXEC, 0644);
    size_t remaining = PIXELS * sizeof(*packed);
    const uint8_t *cursor = (const uint8_t *)packed;
    if (output < 0) return -1;
    while (remaining) {
        ssize_t written = write(output, cursor, remaining);
        if (written <= 0) { close(output); return -1; }
        cursor += (size_t)written;
        remaining -= (size_t)written;
    }
    return close(output);
}

static int capture_single_lane(const char *camera_path, const char *output_path, bool source_is_b) {
    struct camera camera = { .fd = -1 };
    struct v4l2_buffer frame;
    uint64_t *packed = NULL;
    int rc = 1;
    if (start_camera(&camera, camera_path) < 0 || dequeue_frame(&camera, &frame) < 0 ||
        frame.bytesused < CAPTURE_WIDTH * CAPTURE_HEIGHT * 2u) goto done;
    packed = aligned_alloc(64, PIXELS * sizeof(*packed));
    if (!packed) goto done;
    pack_single_yuyv_lane(camera.buffers[frame.index], source_is_b, packed);
    rc = write_packed_frame(output_path, packed) == 0 ? 0 : 1;
done:
    if (rc) fprintf(stderr, "single UVC capture/pack failed: %s\n", strerror(errno));
    free(packed);
    close_camera(&camera);
    return rc;
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
    if (argc == 3 && strcmp(argv[1], "--probe") == 0) return probe_camera(argv[2]);
    if (argc == 4 && strcmp(argv[1], "--single-a") == 0)
        return capture_single_lane(argv[2], argv[3], false);
    if (argc == 4 && strcmp(argv[1], "--single-b") == 0)
        return capture_single_lane(argv[2], argv[3], true);
    if (argc == 4 && strcmp(argv[1], "--mjpeg-stream-test") == 0) {
        struct camera a = { .fd = -1 }, b = { .fd = -1 };
        requested_pixelformat = V4L2_PIX_FMT_MJPEG;
        int rc = (start_camera(&a, argv[2]) < 0 || start_camera(&b, argv[3]) < 0);
        if (!rc) puts("DUAL_MJPEG_STREAMON_PASS");
        close_camera(&a); close_camera(&b); return rc;
    }
    const char *path_a = argc > 1 ? argv[1] : "/dev/video0";
    const char *path_b = argc > 2 ? argv[2] : "/dev/video2";
    const char *output_path = argc > 3 ? argv[3] : "dual_rgb888_640x480.bin";
    struct camera a = { .fd = -1 }, b = { .fd = -1 };
    struct v4l2_buffer frame_a, frame_b;
    uint64_t *packed = NULL;
    int rc = 1;
    if (start_camera(&a, path_a) < 0 || start_camera(&b, path_b) < 0 ||
        dequeue_frame(&a, &frame_a) < 0 || dequeue_frame(&b, &frame_b) < 0 ||
        frame_a.bytesused < CAPTURE_WIDTH * CAPTURE_HEIGHT * 2u ||
        frame_b.bytesused < CAPTURE_WIDTH * CAPTURE_HEIGHT * 2u) goto done;
    packed = aligned_alloc(64, PIXELS * sizeof(*packed));
    if (!packed) goto done;
    pack_dual_yuyv(a.buffers[frame_a.index], b.buffers[frame_b.index], packed);
    rc = write_packed_frame(output_path, packed) == 0 ? 0 : 1;
done:
    if (rc) fprintf(stderr, "UVC capture/pack failed: %s\n", strerror(errno));
    free(packed); close_camera(&a); close_camera(&b); return rc;
}
