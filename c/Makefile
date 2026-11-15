CC      ?= cc
CXX     ?= c++
PYTHON  ?= python3
CFLAGS  ?= -std=c99 -O2 -Wall -Wextra -Wpedantic -Werror
CXXFLAGS?= -std=c++11 -O2 -Wall -Wextra -Werror
SANITIZE?= -fsanitize=address,undefined -fno-omit-frame-pointer

BUILD   := build
VECTORS := ../vectors/mecp-vectors.json

.PHONY: all test clean

all: $(BUILD)/libmecp.a

$(BUILD):
	mkdir -p $@

$(BUILD)/mecp.o: src/mecp.c include/mecp.h | $(BUILD)
	$(CC) $(CFLAGS) -Iinclude -c $< -o $@

$(BUILD)/libmecp.a: $(BUILD)/mecp.o
	$(AR) rcs $@ $^

$(BUILD)/vectors.h: $(VECTORS) tests/gen_vectors.py | $(BUILD)
	$(PYTHON) tests/gen_vectors.py $< $@

# Test binary built from C, with sanitizers.
$(BUILD)/test_c: tests/test_vectors.c src/mecp.c include/mecp.h $(BUILD)/vectors.h
	$(CC) $(CFLAGS) $(SANITIZE) -Iinclude -I$(BUILD) tests/test_vectors.c src/mecp.c -o $@

# Same tests compiled as C++ against the C library, to check the header.
$(BUILD)/test_cpp: tests/test_vectors.c $(BUILD)/mecp.o include/mecp.h $(BUILD)/vectors.h
	$(CXX) $(CXXFLAGS) -x c++ -Iinclude -I$(BUILD) tests/test_vectors.c -x none $(BUILD)/mecp.o -o $@

test: $(BUILD)/test_c $(BUILD)/test_cpp
	./$(BUILD)/test_c
	./$(BUILD)/test_cpp

clean:
	rm -rf $(BUILD)
