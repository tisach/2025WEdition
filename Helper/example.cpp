#include <iostream>
#include "stopwatch.h"

// Example function to measure
void simulated_work(int iterations) {
    volatile int sum = 0;
    for (int i = 0; i < iterations; i++) {
        sum += i;
    }
}

int main() {
    Stopwatch sw;
    
    std::cout << "=== Stopwatch Example ===" << std::endl;
    std::cout << std::endl;
    
    // Example 1: Simple timing
    std::cout << "Example 1: Basic timing" << std::endl;
    sw.start();
    simulated_work(10000000);
    sw.stop();
    
    std::cout << "  Elapsed: " << sw.elapsed_milliseconds() << " ms" << std::endl;
    std::cout << "  Elapsed: " << sw.elapsed_microseconds() << " μs" << std::endl;
    std::cout << std::endl;
    
    // Example 2: Lap timing
    std::cout << "Example 2: Lap timing" << std::endl;
    sw.reset();
    sw.start();
    
    simulated_work(5000000);
    double lap1 = sw.lap();
    std::cout << "  Lap 1: " << lap1 * 1000 << " ms" << std::endl;
    
    simulated_work(3000000);
    double lap2 = sw.lap();
    std::cout << "  Lap 2: " << lap2 * 1000 << " ms" << std::endl;
    
    simulated_work(2000000);
    double lap3 = sw.lap();
    std::cout << "  Lap 3: " << lap3 * 1000 << " ms" << std::endl;
    
    sw.stop();
    std::cout << "  Total: " << sw.elapsed_milliseconds() << " ms" << std::endl;
    std::cout << std::endl;
    
    // Example 3: Pause and resume
    std::cout << "Example 3: Pause and resume" << std::endl;
    sw.reset();
    sw.start();
    simulated_work(5000000);
    sw.stop();
    double time1 = sw.elapsed_milliseconds();
    std::cout << "  After first run: " << time1 << " ms" << std::endl;
    
    sw.start();  // Resume
    simulated_work(5000000);
    sw.stop();
    double time2 = sw.elapsed_milliseconds();
    std::cout << "  After resume: " << time2 << " ms" << std::endl;
    std::cout << "  (Should be ~2x the first run)" << std::endl;
    
    return 0;
}
