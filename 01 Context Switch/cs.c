#include <time.h>
#include <stdio.h>
#include <sys/syscall.h>
#include <unistd.h>

int main ( int argc, char *argv[] ) {

    // Number of iterations
    int iterations = 100000000;

    // Measure time
    clock_t start = clock();

    // System call loop
    for (int i = 0; i < iterations; i++) {
        syscall(SYS_getpid);
        // sleep(0); // if the syscall function doesn't exist or is deprecated
    }

    // Messure time
    clock_t end = clock();
    double time_spent = (double)(end - start) / CLOCKS_PER_SEC;
    printf("Time taken: %f seconds\n", time_spent);
    printf("Iterations: %d\n", iterations);
    printf("Average time per call: %f microseconds\n", (time_spent / iterations) * 1000000);
    return 0;
}
