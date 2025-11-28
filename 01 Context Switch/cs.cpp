#include <iostream>
#include <sys/syscall.h>
#include <unistd.h>
#include "stopwatch.h"

int main(int argc, char *argv[]) {

    // Number of iterations
    int iterations = 100000000;

    // Create stopwatch
    Stopwatch sw;

    // Measure time
    sw.start();

    // System call loop
    for (int i = 0; i < iterations; i++) {
        syscall(SYS_getpid);
        // sleep(0); // if the syscall function doesn't exist or is deprecated
    }

    // Stop measurement
    sw.stop();

    double time_spent = sw.elapsed_seconds();
    
    std::cout << "Time taken: " << time_spent << " seconds" << std::endl;
    std::cout << "Iterations: " << iterations << std::endl;
    std::cout << "Average time per call: " << sw.elapsed_microseconds() / iterations << " microseconds" << std::endl;
    
    return 0;
}
