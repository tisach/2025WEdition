# Makefile for Helper Library
# This builds a static library from all C++ classes in the Helper folder

# Compiler settings
CXX = g++
CXXFLAGS = -std=c++11 -Wall -Wextra -O2 -fPIC
AR = ar
ARFLAGS = rcs

# Directory structure
SRC_DIR = src
INC_DIR = include
OBJ_DIR = obj
LIB_DIR = lib

# Library name
LIB_NAME = libhelper.a
LIB_PATH = $(LIB_DIR)/$(LIB_NAME)

# Find all source files
SOURCES = $(wildcard $(SRC_DIR)/*.cpp)
OBJECTS = $(patsubst $(SRC_DIR)/%.cpp,$(OBJ_DIR)/%.o,$(SOURCES))
HEADERS = $(wildcard $(INC_DIR)/*.h)

# Phony targets
.PHONY: all clean install help

# Default target
all: $(LIB_PATH)

# Build the static library
$(LIB_PATH): $(OBJECTS) | $(LIB_DIR)
	@echo "Creating static library: $@"
	$(AR) $(ARFLAGS) $@ $^
	@echo "Library created successfully!"

# Compile source files to object files
$(OBJ_DIR)/%.o: $(SRC_DIR)/%.cpp $(HEADERS) | $(OBJ_DIR)
	@echo "Compiling: $<"
	$(CXX) $(CXXFLAGS) -I$(INC_DIR) -c $< -o $@

# Create directories if they don't exist
$(OBJ_DIR):
	mkdir -p $(OBJ_DIR)

$(LIB_DIR):
	mkdir -p $(LIB_DIR)

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf $(OBJ_DIR)/*.o $(LIB_PATH)
	@echo "Clean complete!"

# Clean everything including directories
distclean: clean
	@echo "Removing all generated directories..."
	rm -rf $(OBJ_DIR) $(LIB_DIR)
	@echo "Distclean complete!"

# Install headers and library to system (optional)
install: all
	@echo "Installing library and headers..."
	@echo "Note: This is a local project. Use -I and -L flags to link."
	@echo "  Include path: -I$(shell pwd)/$(INC_DIR)"
	@echo "  Library path: -L$(shell pwd)/$(LIB_DIR) -lhelper"

# Help target
help:
	@echo "Helper Library Makefile"
	@echo "======================"
	@echo "Targets:"
	@echo "  all       - Build the static library (default)"
	@echo "  clean     - Remove object files and library"
	@echo "  distclean - Remove all generated files and directories"
	@echo "  install   - Show how to link against this library"
	@echo "  help      - Show this help message"
	@echo ""
	@echo "Directory structure:"
	@echo "  $(SRC_DIR)/     - Source files (*.cpp)"
	@echo "  $(INC_DIR)/     - Header files (*.h)"
	@echo "  $(OBJ_DIR)/     - Object files (*.o) [generated]"
	@echo "  $(LIB_DIR)/     - Library file [generated]"
	@echo ""
	@echo "To use this library in your project:"
	@echo "  g++ -std=c++11 -I$(shell pwd)/$(INC_DIR) your_program.cpp -L$(shell pwd)/$(LIB_DIR) -lhelper -o your_program"
