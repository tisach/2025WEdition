#ifndef STOPWATCH_H
#define STOPWATCH_H

#include <chrono>

/**
 * @brief A classical stopwatch abstraction for measuring execution times
 * 
 * This class provides a simple interface to measure elapsed time with
 * high-resolution timing capabilities. It supports basic stopwatch operations:
 * start, stop, reset, and lap timing.
 */
class Stopwatch {
public:
    /**
     * @brief Constructor - creates a stopwatch in stopped state
     */
    Stopwatch();

    /**
     * @brief Start or resume the stopwatch
     */
    void start();

    /**
     * @brief Stop the stopwatch
     */
    void stop();

    /**
     * @brief Reset the stopwatch to zero (also stops it)
     */
    void reset();

    /**
     * @brief Record a lap time without stopping the stopwatch
     * @return Elapsed time since last lap (or start) in seconds
     */
    double lap();

    /**
     * @brief Get the elapsed time in seconds
     * @return Total elapsed time in seconds
     */
    double elapsed_seconds() const;

    /**
     * @brief Get the elapsed time in milliseconds
     * @return Total elapsed time in milliseconds
     */
    double elapsed_milliseconds() const;

    /**
     * @brief Get the elapsed time in microseconds
     * @return Total elapsed time in microseconds
     */
    double elapsed_microseconds() const;

    /**
     * @brief Get the elapsed time in nanoseconds
     * @return Total elapsed time in nanoseconds
     */
    long long elapsed_nanoseconds() const;

    /**
     * @brief Check if the stopwatch is currently running
     * @return true if running, false if stopped
     */
    bool is_running() const;

private:
    using Clock = std::chrono::high_resolution_clock;
    using TimePoint = std::chrono::time_point<Clock>;
    using Duration = std::chrono::nanoseconds;

    TimePoint start_time_;      // Time when started/resumed
    TimePoint last_lap_time_;   // Time of last lap
    Duration accumulated_time_; // Total accumulated time
    bool running_;              // Whether stopwatch is running

    /**
     * @brief Get current elapsed duration
     * @return Duration since start plus accumulated time
     */
    Duration get_elapsed_duration() const;
};

#endif // STOPWATCH_H
