/*
 * pulse_heartbeat.c — a small periodic heartbeat for QNX 8.0.
 *
 * On QNX it uses a CLOCK_MONOTONIC timer and SCHED_FIFO so the pulse
 * stays on budget. On a host OS, `make host` builds a smoke test with
 * POSIX clocks so the logic can be reviewed without the SDP installed.
 *
 * This is a developer-tooling demo (a lantern / line heartbeat), not
 * a safety-certified device.
 */

#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#ifndef HOST_BUILD
#include <sched.h>
#include <sys/neutrino.h>
#endif

#define PERIOD_NS 10000000L /* 10 ms */
#define MAX_LATE_NS 2000000L
#define LOOPS 50

static void die(const char *msg) {
    perror(msg);
    exit(1);
}

static void add_ns(struct timespec *ts, long ns) {
    ts->tv_nsec += ns;
    while (ts->tv_nsec >= 1000000000L) {
        ts->tv_nsec -= 1000000000L;
        ts->tv_sec += 1;
    }
}

static long diff_ns(const struct timespec *later, const struct timespec *earlier) {
    return (later->tv_sec - earlier->tv_sec) * 1000000000L + (later->tv_nsec - earlier->tv_nsec);
}

static int setup_realtime(void) {
#ifndef HOST_BUILD
    struct sched_param param;
    memset(&param, 0, sizeof(param));
    param.sched_priority = 21;
    if (sched_setscheduler(0, SCHED_FIFO, &param) != 0) {
        return -1;
    }
#endif
    return 0;
}

int main(void) {
    struct timespec next;
    int late = 0;
    int i;

    if (setup_realtime() != 0) {
        fprintf(stderr, "sched_setscheduler(SCHED_FIFO, 21) failed: %s\n", strerror(errno));
        fprintf(stderr, "continuing so the demo still runs in unprivileged QEMU\n");
    }

    if (clock_gettime(CLOCK_MONOTONIC, &next) != 0) {
        die("clock_gettime");
    }
    add_ns(&next, PERIOD_NS);

    printf("pulse_heartbeat start, period=10ms\n");
    fflush(stdout);

    for (i = 0; i < LOOPS; i++) {
        struct timespec now;
        long slack;

        if (clock_nanosleep(CLOCK_MONOTONIC, TIMER_ABSTIME, &next, NULL) != 0) {
            die("clock_nanosleep");
        }
        if (clock_gettime(CLOCK_MONOTONIC, &now) != 0) {
            die("clock_gettime");
        }
        slack = diff_ns(&now, &next);
        if (slack > MAX_LATE_NS) {
            late += 1;
            fprintf(stderr, "pulse %d late by %ld ns\n", i, slack);
        } else {
            printf("pulse %d ok (late %ld ns)\n", i, slack);
        }
        fflush(stdout);
        add_ns(&next, PERIOD_NS);
    }

    printf("pulse_heartbeat done, late=%d/%d\n", late, LOOPS);
    return late == 0 ? 0 : 2;
}
