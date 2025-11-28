CC = gcc
CXX = g++

CFLAGS = -O3
CXXFLAGS = -std=c++11 -O3 -I../Helper/include
LDFLAGS = -L../Helper/lib -lhelper

TARGET_C = cs
TARGET_CXX = cs_cpp
SRC_C = cs.c
SRC_CXX = cs.cpp

all: $(TARGET_C) $(TARGET_CXX)

# C version (original)
$(TARGET_C): $(SRC_C)
	$(CC) $(CFLAGS) -o $(TARGET_C) $(SRC_C)

# C++ version with stopwatch
$(TARGET_CXX): $(SRC_CXX)
	cd ../Helper && $(MAKE)
	$(CXX) $(CXXFLAGS) -o $(TARGET_CXX) $(SRC_CXX) $(LDFLAGS)

clean:
	rm -f $(TARGET_C) $(TARGET_CXX)

run: $(TARGET_C)
	./$(TARGET_C)

run_cpp: $(TARGET_CXX)
	./$(TARGET_CXX)

.PHONY: all clean run run_cpp
