/*
Trivial blocked matrix multiply.

Written by Charles Reiss.

To the extent possible under law, I waive all copyright and related or neighboring rights 
to this file.
 */

#define _XOPEN_SOURCE 700
#include <assert.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdio.h>

// Allow easy switching between float and double
typedef float myfloat;

void random_matrix(myfloat *A, int I, int J) {
    for (int i = 0; i < I; ++i) {
        for (int j = 0; j < J; ++j) {
            A[i * J + j] = drand48();
        }
    }
}

void print_matrix(myfloat *A, int I, int J) {
    for (int i = 0; i < I; ++i) {
        for (int j = 0; j < J; ++j) {
            fprintf(stdout,"%f ", A[i * J + j]);
        }
        printf("\n"); 
    }
}

/* computes matrix multiply C += A * B
 * A is I by K, B is K by J, C is I by J 
 */
void blocked_matmul(myfloat * restrict A, myfloat * restrict B, myfloat * restrict C, int I, int K, int J) {
    assert(I % 2 == 0);
    assert(J % 2 == 0);
    assert(K % 2 == 0);
    for (int i = 0; i < I; i += 2) {
        for (int j = 0; j < J; j += 2) {
            myfloat Ci0j0 = C[(i + 0) * J + (j + 0)];
            myfloat Ci0j1 = C[(i + 0) * J + (j + 1)];
            myfloat Ci1j0 = C[(i + 1) * J + (j + 0)];
            myfloat Ci1j1 = C[(i + 1) * J + (j + 1)];
            for (int k = 0; k < K; k += 2) {
                myfloat Ai0k0 = A[(i + 0) * K + (k + 0)];
                myfloat Ai0k1 = A[(i + 0) * K + (k + 1)];
                myfloat Ai1k0 = A[(i + 1) * K + (k + 0)];
                myfloat Ai1k1 = A[(i + 1) * K + (k + 1)];
                myfloat Bk0j0 = B[(k + 0) * J + (j + 0)];
                myfloat Bk0j1 = B[(k + 0) * J + (j + 1)];
                myfloat Bk1j0 = B[(k + 1) * J + (j + 0)];
                myfloat Bk1j1 = B[(k + 1) * J + (j + 1)];

                Ci0j0 += Ai0k0 * Bk0j0 + Ai0k1 * Bk1j0;
                Ci1j0 += Ai1k0 * Bk0j0 + Ai1k1 * Bk1j0;
                Ci0j1 += Ai0k0 * Bk0j1 + Ai0k1 * Bk1j1;
                Ci1j1 += Ai1k0 * Bk0j1 + Ai1k1 * Bk1j1;
            }
            C[(i + 0) * J + (j + 0)] = Ci0j0;
            C[(i + 0) * J + (j + 1)] = Ci0j1;
            C[(i + 1) * J + (j + 0)] = Ci1j0;
            C[(i + 1) * J + (j + 1)] = Ci1j1;
        }
    }
}

uint64_t read_tsc(void) {
#ifdef __i386__
    uint32_t hi, lo;
#else
    uint64_t hi, lo;
#endif
    /* 
     * Embed the assembly instruction 'rdtsc', which should not be relocated (`volatile').
     *  The instruction will modify r_a_x and r_d_x, which the compiler should map to
     * lo and hi, respectively.
     * 
     * The format for GCC-style inline assembly generally is:
     * __asm__ ( ASSEMBLY CODE : OUTPUTS : INPUTS : OTHER THINGS CHANGED )
     *
     * Note that if you do not (correctly) specify the side effects of an assembly operation, the
     * compiler may assume that other registers and memory are not affected. This can easily
     * lead to cases where your program will produce difficult-to-debug wrong answers when
     * optimizations are enabled.
     */
    __asm__ volatile ( "rdtsc" : "=a"(lo), "=d"(hi));
#ifdef __i386__
    return lo | ((uint64_t) hi << 32);
#else
    return lo | (hi << 32);
#endif
}

#define MAX_SIZE 110

static myfloat A[MAX_SIZE * MAX_SIZE];
static myfloat B[MAX_SIZE * MAX_SIZE];
static myfloat C[MAX_SIZE * MAX_SIZE];

//A is I by K, B is K by J, C is I by J 
int main(int argc, char* argv[]) {
    srand48(1); // fixed seed for reproducible results
    if (argc != 4){
        fprintf(stderr, "%s\n", "Wrong use of command!");
        fprintf(stdout, "%s %s %s\n", "Help: ", argv[0] , "I J K");
        fprintf(stdout, "%s %s %s\n", "Example: ", argv[0] , "10 20 30");
        printf("Blocked matmul computes matrix multiply C += A * B\n");
        printf("A is I by K, B is K by J, C is I by J\n");
        printf("Where I J and K are divisible by two\n");
        return 1;
    }
    int I  = atoi(argv[1]);
    int J  = atoi(argv[2]);
    int K  = atoi(argv[3]);
    random_matrix(A, I, K);
    random_matrix(B, K, J);
    random_matrix(C, I, J);
    // printf("A:\n");
    // print_matrix(A, I, K);
    // printf("B:\n");
    // print_matrix(B, K, J);
    // printf("C:\n");
    // print_matrix(C, I, J);
    for (int i = 0; i < 4; ++i) {
        long start = read_tsc();
        blocked_matmul(A, B, C, I, J, K);
        long end = read_tsc();
        printf("Iteration %d: %ld cycles\n", i, end - start);
    }
    // printf("Result:\n");
    // print_matrix(C, I, J);
}
