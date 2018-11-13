CC = gcc
CFLAGS_MATMUL = -g -O3 -std=c99 -ffinite-math-only -fno-signaling-nans -fcx-limited-range -fno-math-errno \
         -fno-trapping-math -fassociative-math -fno-signed-zeros -ftree-vectorize
CFLAG_UNROLL =  -funroll-loops

CFLAGS = -g -O3 -std=c99

BINARIES = blocked-matmul blocked-matmul-no-unroll queens 

SOURCES = gem5script.py blocked-matmul.c queens.c

DOCS = README.md

# default target
all: $(BINARIES)

blocked-matmul: blocked-matmul.c
				$(CC) $(CFLAGS_MATMUL) $(CFLAG_UNROLL)  blocked-matmul.c -o  blocked-matmul

blocked-matmul-no-unroll: blocked-matmul.c
				$(CC) $(CFLAGS_MATMUL) blocked-matmul.c -o  blocked-matmul-no-unroll



queens: queens.c
	$(CC) $(CFLAGS) $< -o $@


clean:
	rm -f $(BINARIES)


.PHONY: all clean 
