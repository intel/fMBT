# autodebug and valgrind-autodebug

autodebug prints human-readable debug information on crashes and
issues found by AddressSanitizer and Valgrind.


Example 1: Debug a crashing program
-----------------------------------

1. Have some bad code
   ```
   int main(int argc, char** argv)
   {
       char* last_arg = argv[argc];
       char first_letter = last_arg[0];
       return (int)first_letter;
   }
   ```

2. Build it with debug information
   ```
   gcc -o myprog -g -O0 myprog.c
   ```

3. Crash!?
   ```
   $ ./myprog
   Segmentation fault
   ```

4. Use autodebug to give more information
   ```
   $ autodebug ./myprog
   ========================================================================
   error 1: Program received signal SIGSEGV, Segmentation fault.
   error in main (myprog.c:4)
        arguments:
            argc = 1
            argv = 0x7fffffffe0c8
        local variables:
            first_letter = 0 '\000'
            last_arg = 0x0
        error at line 4:
            1       int main(int argc, char** argv)
            2       {
            3           char* last_arg = argv[argc];
            4           char first_letter = last_arg[0];
            5           return (int)first_letter;
            6       }
        nearby expressions:
            argc = 1
            argv = (char **) 0x7fffffffe0c8
            argv[argc] = 0x0
            first_letter = 0 '\000'
            last_arg = 0x0
            main = {int (int, char **)} 0x5555555545fa <main>
        ```

Example 2: Post-mortem debug a crashed program
----------------------------------------------

1. Make sure core gets dumped on a crash, then run a program that crashes
   ```
   $ ulimit -c unlimited
   $ ./myprog
   Segmentation fault (core dumped)
   ```

2. Use autodebug to print details from the core without rerunning the program.
   ```
   $ autodebug -c core
   ========================================================================
   error: Program terminated with signal SIGSEGV, Segmentation fault.
   error in main (myprog.c:4)
       arguments:
           argc = 1
           argv = 0x7ffd9105df98
       local variables:
           first_letter = 0 '\000'
           last_arg = 0x0
       error at line 4:
           1	int main(int argc, char** argv)
           2	{
           3	    char* last_arg = argv[argc];
           4	    char first_letter = last_arg[0];
           5	    return (int)first_letter;
           6	}
       nearby expressions:
           argc = 1
           argv = (char **) 0x7ffd9105df98
           argv[argc] = 0x0
           first_letter = 0 '\000'
           last_arg = 0x0
           main = {int (int, char **)} 0x5593d36255fa <main>
   ```

Example 3: Debug issues reported by valgrind
--------------------------------------------

1. Replace ``valgrind`` with ``valgrind-autodebug`` when you run a
   program.
   ```
   $ valgrind-autodebug ./myprog
   ========================================================================
   error 1: Invalid read of size 1
   error in main (myprog.c:4)
       arguments:
           argc = 1
           argv = 0x1fff0000d8
       local variables:
           first_letter = 0 '\000'
           last_arg = 0x0
       error at line 4:
           1	int main(int argc, char** argv)
           2	{
           3	    char* last_arg = argv[argc];
           4	    char first_letter = last_arg[0];
           5	    return (int)first_letter;
           6	}
       nearby expressions:
           argc = 1
           argv = (char **) 0x1fff0000d8
           argv[argc] = 0x0
           first_letter = 0 '\000'
           last_arg = 0x0
           main = {int (int, char **)} 0x1085fa <main>
   ```
