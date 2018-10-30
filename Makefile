CC = gcc
CFLAGS_MATMUL = -g -O3 -std=c99 -ffinite-math-only -fno-signaling-nans -fcx-limited-range -fno-math-errno \
         -fno-trapping-math -fassociative-math -fno-signed-zeros -funroll-loops -ftree-vectorize

CFLAGS = -g -O3 -std=c99

BINARIES = blocked-matmul queens 

SOURCES = gem5script.py blocked-matmul.c queens.c

DOCS = README.md

# default target
all: $(BINARIES)

blocked-matmul: CFLAGS = $(CFLAGS_MATMUL)
blocked-matmul: blocked-matmul.c


queens: queens.c
	$(CC) $(CFLAGS) $< -o $@


clean:
	rm -f $(BINARIES)


.PHONY: all clean 
