# Codelab: Check a QNX 8.0 project on the host before you boot QEMU

This is a short tutorial for the QNX Global Hackathon “Best Codelab / Tutorial” bonus prize. It uses the `schedgate` tool in this repository. You do not need a QNX license to follow the first half.

## What you will do

1. Inspect a thread budget with no SDP installed.
2. Read the findings on a broken fixture.
3. (Optional) Build the heartbeat demo on a host, then rebuild it with qcc once QNX Everywhere is installed.

## 1. Run the host tool

From the repository root:

```bash
python3 schedgate.py samples/qnx-heartbeat --html report.html
```

You should see two threads (`pulse_loop` at SCHED_FIFO 21, `logger` at SCHED_RR 10), a periodic utilization of 0.160, and a Liu-Layland bound of about 0.828. The set is schedulable. The tool also reads `ifs.build` and `Makefile` for world-writable IFS entries, missing `waitfor` lines, and Makefiles that never mention `qcc` or `QNX_TARGET`.

## 2. See a failing budget on purpose

```bash
python3 schedgate.py schedgate/fixtures/bad
```

This fixture is meant to fail. Expect at least:

- `other-on-deadline` — a periodic thread left on `SCHED_OTHER`
- `wcet-exceeds-period` — a WCET longer than the period
- `ifs-world-writable` — an IFS entry with mode 0777
- `make-host-gcc-only` — a Makefile with host gcc and no qcc path

Exit status is 1 when any error is present, so you can put `schedgate` in CI on the host before anyone spends time on QEMU.

## 3. Build the heartbeat (host first, QNX second)

Host smoke test, no QNX required:

```bash
cc -DHOST_BUILD -Wall -Werror -O2 -o pulse_heartbeat samples/qnx-heartbeat/pulse_heartbeat.c
./pulse_heartbeat
```

The program fires 50 pulses on a 10 ms CLOCK_MONOTONIC schedule and exits 0 if none are more than 2 ms late.

On a machine with QNX Everywhere / QNX SDP 8.0:

```bash
source qnxsdp-env.sh   # use the env script that ships with your install
cd samples/qnx-heartbeat
make qnx
```

`make qnx` refuses to run if `QNX_TARGET` is unset, so a host-only `make host` cannot be mistaken for a QNX build. Copy `nto/x86_64/o/pulse_heartbeat` into your IFS, boot the QNX 8.0 image in QEMU, and run the same binary on the target.

## Why this belongs on QNX

A periodic heartbeat is only honest if the budget, the scheduling policy, and the image it ships in all agree. `schedgate` checks the budget and the image on the host. `pulse_heartbeat` is the small target program that budget describes.

## AI disclosure

This project was designed and built by Luis Alfredo Salazar Courtois, with assistance from an AI system under his direction.
