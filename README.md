# gdb-heap-overflow-detection
Detects heap overflows using GDB. Provides extended breakpoint objects to assist in automation. Needs more extensive testing

USE:

gdb -q -x overflow-detection.py


Edit do-input.py to trigger the overflow in your application. If the overflow is directly from an input string, you can use getString to generate a pattern and it will tell you the offset of the next chunk metadata with padding/allignment detection.

Tested on GDB v7.9 with Babys First Heap from defcon 2014 quals

TODO:
modify the watchpoint removal code as doing self.delete() from within a watchpoint stop event causes a segfault in gdb 7.9 (granted is undefined behaviour and directly dissallowed in the docs)
