# Dual build: host smoke test with gcc, QNX 8.0 with qcc.
ifndef QNX_TARGET
host:
	gcc -DHOST_BUILD -Wall -Werror -o pulse_heartbeat pulse_heartbeat.c
else
ARTIFACT=$(PWD)/nto/x86_64/o/pulse_heartbeat
CC=qcc
CFLAGS=-Vgcc_ntox86_64 -O2 -Wall -fno-common
pulse:
	$(CC) $(CFLAGS) -o $(ARTIFACT) pulse_heartbeat.c
endif
