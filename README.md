# OS-Level Experiments (Winter 2025)

## Helper

A reusable library of utility classes for timing and measurements across all experiments.

### Content

- **Stopwatch class**: High-resolution timing abstraction using `std::chrono`
  - `include/stopwatch.h`: Header file
  - `src/stopwatch.cpp`: Implementation
  - Supports start/stop, lap timing, and multiple time units (seconds, milliseconds, microseconds, nanoseconds)

### Structure

```
Helper/
├── include/       # Public headers
├── src/           # Implementation files
├── lib/           # Compiled static library (libhelper.a)
└── Makefile       # Build system
```

### Usage

```bash
cd Helper
make
```

Link in your programs:
```bash
g++ -std=c++11 -IHelper/include your_program.cpp -LHelper/lib -lhelper -o your_program
```

See `Helper/README.md` for detailed documentation.

---

## 01 Context Switch

This folder contains experiments to measure the cost of context switches and system calls at the OS level.

### Content

- **cs.c**: Original C program that measures the average time of system calls using `clock()` for timing

- **cs.cpp**: Improved C++ version that uses the Stopwatch class from the Helper library for high-resolution timing measurements

- **Python Wrapper**: A Python-based wrapper that allows importing and calling C/C++ functions:
  - `cs.py`: Main Python script that uses the `Importer` utility to execute context switch measurements from both C and C++ implementations
  - `cs.c` & `cs.cpp`: C and C++ implementations with a `measure_context_switch()` function
  - `lib/Importer.py`: Utility for dynamically importing and executing C/C++ code from Python
  - `requirements.txt`: Python dependencies for the wrapper

- **Makefile**: Build configuration for compiling both C and C++ versions

- **todo.md**: Future improvements and completed tasks

### Usage

Compile and run the C version:
```bash
cd "01 Context Switch"
make cs
./cs
```

Compile and run the C++ version (with Stopwatch):
```bash
cd "01 Context Switch"
make cs_cpp
./cs_cpp
```

Build both versions:
```bash
cd "01 Context Switch"
make all
```

Or use the Python wrapper (requires gcc/g++):
```bash
cd "01 Context Switch/Python Wrapper"
pip install -r requirements.txt
python cs.py
```


