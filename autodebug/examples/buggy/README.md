# Debugging buggy.c with autodebug, Valgrind and AddressSanitizer

Preparing the example
---------------------

1. Check out buggy.c. It has three errors:

   * ``./buggy p`` will read memory through invalid pointer.

   * ``./buggy s`` will write to array in stack, but uses index -2.

   * ``./buggy u`` will compare uninitialized memory to a value in ``if``.


2. Build ``buggy`` (debug build) and ``buggy-s`` (debug build instrumented by AddressSanitizer) binaries.
```
$ make buggy buggy-s
gcc -O0 -g -o buggy buggy.c
gcc -O0 -g -fsanitize=address -fsanitize-recover=address -o buggy-s buggy.c
```

Find and debug the errors
-------------------------

1. Invalid pointer. Easy to find by just running the program:
   ```
   $ ./buggy p
   Segmentation fault
   ```

   Debug with:
   $ autodebug ./buggy p
   ========================================================================
   error 1: Program received signal SIGSEGV, Segmentation fault.
   error in example_bad_ptr (buggy.c:5)
       arguments:
           i = 2
       local variables:
           memory_at_address_i = 0x2
       error at line 5:
           1	/* file: buggy.c */
           2	#include <stdlib.h>
           3	int example_bad_ptr(long i) {
           4	    int* memory_at_address_i = (int*)i;
           5	    return *memory_at_address_i;
           6	}
           7	void example_stack(int i) {
           8	    int array_in_stack[2];
           9	    array_in_stack[0-i] = i;
           10	}
       ...
   ```

2. Stack underflow. Cannot be foundby running the program:
   ```
   $ ./buggy s
   $
   ```

   ...and cannot be found with valgrind:
   ```
   $ valgrind ./buggy s
   ==27560== Memcheck, a memory error detector
   ==27560== Copyright (C) 2002-2017, and GNU GPL'd, by Julian Seward et al.
   ==27560== Using Valgrind-3.13.0 and LibVEX; rerun with -h for copyright info
   ==27560== Command: ./buggy s
   ==27560==
   ==27560==
   ==27560== HEAP SUMMARY:
   ==27560==     in use at exit: 0 bytes in 0 blocks
   ==27560==   total heap usage: 0 allocs, 0 frees, 0 bytes allocated
   ==27560==
   ==27560== All heap blocks were freed -- no leaks are possible
   ==27560==
   ==27560== For counts of detected and suppressed errors, rerun with: -v
   ==27560== ERROR SUMMARY: 0 errors from 0 contexts (suppressed: 0 from 0)
   ```

   The error can be found with AddressSanitizer-instrumented executable:
   ```
   $ ./buggy-s s
   =================================================================
   ==27573==ERROR: AddressSanitizer: stack-buffer-underflow on address 0x7ffcc4318e58 at pc 0x5585d86082df bp 0x7ffcc4318e20 sp 0x7ffcc4318e18
   WRITE of size 4 at 0x7ffcc4318e58 thread T0
       #0 0x5585d86082de in example_stack /home/ask/git/autodebug/examples/buggy/buggy.c:9
       #1 0x5585d8608454 in main /home/ask/git/autodebug/examples/buggy/buggy.c:19
       #2 0x7f9762fb8b16 in __libc_start_main ../csu/libc-start.c:310
       #3 0x5585d86080f9 in _start (/home/ask/git/autodebug/examples/buggy/buggy-s+0x10f9)

   Address 0x7ffcc4318e58 is located in stack of thread T0 at offset 24 in frame
       #0 0x5585d8608217 in example_stack /home/ask/git/autodebug/examples/buggy/buggy.c:7

     This frame has 1 object(s):
       [32, 40) 'array_in_stack' <== Memory access at offset 24 underflows this variable
   ...
   ```

   Autodebug gives familiar output also from AddressSanitizer errors:
   ```
   $ autodebug ./buggy-s s
   ========================================================================
   error 1: AddressSanitizer found stack-buffer-underflow
   error in example_stack (buggy.c:9)
       arguments:
           i = 2
       local variables:
           array_in_stack = {0, 0}
       error at line 9:
           4	    int* memory_at_address_i = (int*)i;
           5	    return *memory_at_address_i;
           6	}
           7	void example_stack(int i) {
           8	    int array_in_stack[2];
           9	    array_in_stack[0-i] = i;
           10	}
           11	void example_uninit(int i) {
           12	    char* s = (char*)malloc(4);
           13	    if (s[i] == 0) return;
       nearby expressions:
           0-i = -2
           array_in_stack[2] = 0
           ...
   ```

3. Uninitialized value in condition. Cannot be found by running the program or the instrumented version:
   ```
   $ ./buggy u
   $ ./buggy-s u
   $
   ```
   Valgrind finds the error:
   ```
   $ valgrind ./buggy u
   ==27620== Memcheck, a memory error detector
   ==27620== Copyright (C) 2002-2017, and GNU GPL'd, by Julian Seward et al.
   ==27620== Using Valgrind-3.13.0 and LibVEX; rerun with -h for copyright info
   ==27620== Command: ./buggy u
   ==27620==
   ==27620== Conditional jump or move depends on uninitialised value(s)
   ==27620==    at 0x1091A0: example_uninit (buggy.c:13)
   ==27620==    by 0x109206: main (buggy.c:20)
   ```

   Valgrind-autodebug shows you again in familiar format where the error was and what values where in the variables:
   ```
   $ valgrind-autodebug ./buggy u
   ========================================================================
   error 1: Conditional jump or move depends on uninitialised value(s)
   error in example_uninit (buggy.c:13)
       arguments:
           i = 2
       local variables:
           s = 0x4a2a040 ""
       error at line 13:
           8	    int array_in_stack[2];
           9	    array_in_stack[0-i] = i;
           10	}
           11	void example_uninit(int i) {
           12	    char* s = (char*)malloc(4);
           13	    if (s[i] == 0) return;
           14	    free(s);
           15	}
           16	int main(int argc, char** argv) {
           17	    switch (argv[1][0]) {
       nearby expressions:
           ...
           s = 0x4a2a040 ""
           s[i] = 0 '\000'
   ```
