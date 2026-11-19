# Host smoke test (no QNX required):
#   make host
# QNX SDP 8.0 / QNX Everywhere:
#   source qnxsdp-env.sh   # or the QNX Everywhere env script
#   make qnx
#
# The qnx target uses qcc and requires QNX_TARGET as evidence this
# project is meant to run on QNX 8.0, including under QEMU.

APP=pulse_heartbeat
SRC=pulse_heartbeat.c
CFLAGS_HOST=-DHOST_BUILD -Wall -Werror -O2
CFLAGS_QNX=-Vgcc_ntox86_64 -Wall -Werror -O2 -fno-common

.PHONY: all host qnx clean

all: host

host: $(SRC)
	cc $(CFLAGS_HOST) -o $(APP) $(SRC)

qnx: $(SRC)
ifndef QNX_TARGET
	$(error QNX_TARGET is not set. Source the QNX SDP 8.0 environment first)
endif
	mkdir -p nto/x86_64/o
	qcc $(CFLAGS_QNX) -o nto/x86_64/o/$(APP) $(SRC)

clean:
	rm -f $(APP)
	rm -rf nto
