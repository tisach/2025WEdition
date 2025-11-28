#include "stopwatch.h"

Stopwatch::Stopwatch() 
    : start_time_(), 
      last_lap_time_(),
      accumulated_time_(Duration::zero()),
      running_(false) {
}

void Stopwatch::start() {
    if (!running_) {
        start_time_ = Clock::now();
        last_lap_time_ = start_time_;
        running_ = true;
    }
}

void Stopwatch::stop() {
    if (running_) {
        accumulated_time_ += Clock::now() - start_time_;
        running_ = false;
    }
}

void Stopwatch::reset() {
    accumulated_time_ = Duration::zero();
    running_ = false;
}

double Stopwatch::lap() {
    if (!running_) {
        return 0.0;
    }
    
    TimePoint now = Clock::now();
    Duration lap_duration = now - last_lap_time_;
    last_lap_time_ = now;
    
    return std::chrono::duration<double>(lap_duration).count();
}

double Stopwatch::elapsed_seconds() const {
    auto duration = get_elapsed_duration();
    return std::chrono::duration<double>(duration).count();
}

double Stopwatch::elapsed_milliseconds() const {
    auto duration = get_elapsed_duration();
    return std::chrono::duration<double, std::milli>(duration).count();
}

double Stopwatch::elapsed_microseconds() const {
    auto duration = get_elapsed_duration();
    return std::chrono::duration<double, std::micro>(duration).count();
}

long long Stopwatch::elapsed_nanoseconds() const {
    return get_elapsed_duration().count();
}

bool Stopwatch::is_running() const {
    return running_;
}

Stopwatch::Duration Stopwatch::get_elapsed_duration() const {
    if (running_) {
        return accumulated_time_ + (Clock::now() - start_time_);
    }
    return accumulated_time_;
}
