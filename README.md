# schedgate

A host-side QNX 8.0 readiness linter, plus a 10 ms heartbeat you can boot in QEMU.

**QNX Global Hackathon 2026 entry** — category: Developer Tooling & Host Tools.

`schedgate` reads a `schedgate.yml` thread budget, a QNX IFS buildfile, and a Makefile, then reports rate-monotonic / hyperbolic schedulability and common QNX 8.0 pitfalls: `SCHED_OTHER` on a deadline thread, WCET longer than the period, world-writable IFS entries, host-only gcc Makefiles, and missing `waitfor` lines. It has no third-party Python dependencies.

The companion program, `pulse_heartbeat`, is the small target-side example that budget describes: a 10 ms `CLOCK_MONOTONIC` pulse, `SCHED_FIFO` priority 21 on QNX, and a host smoke test so the logic can be reviewed without the SDP.

## Quick start (no QNX install)

```bash
python3 schedgate.py samples/qnx-heartbeat --html report.html
python3 -m unittest tests/test_schedgate.py
make -C samples/qnx-heartbeat host
./samples/qnx-heartbeat/pulse_heartbeat
```

## QNX 8.0 build

Source the QNX Everywhere / QNX SDP 8.0 environment, then:

```bash
cd samples/qnx-heartbeat
make qnx
```

`make qnx` uses `qcc` and refuses to run if `QNX_TARGET` is unset, so a host-only `make host` cannot be mistaken for a QNX build. Copy `nto/x86_64/o/pulse_heartbeat` into your IFS and boot the QNX 8.0 image in QEMU. A short walkthrough is in [CODELAB.md](CODELAB.md).

The QNX connection in this repository is concrete, not just a README mention: `samples/qnx-heartbeat/Makefile` (`qcc`, `QNX_TARGET`), `pulse_heartbeat.c` (Neutrino `sched_setscheduler` / `SCHED_FIFO` when `HOST_BUILD` is not set), and `ifs.build`.

## License

MIT. See [LICENSE](LICENSE).

## AI disclosure

This project was designed and built by Luis Alfredo Salazar Courtois, with assistance from an AI system under his direction.
