/* file: buggy.c */
#include <stdlib.h>
int example_bad_ptr(long i) {
    int* memory_at_address_i = (int*)i;
    return *memory_at_address_i;
}
void example_stack(int i) {
    int array_in_stack[2];
    array_in_stack[0-i] = i;
}
void example_uninit(int i) {
    char* s = (char*)malloc(4);
    if (s[i] == 0) return;
    free(s);
}
int main(int argc, char** argv) {
    switch (argv[1][0]) {
    case 'p': example_bad_ptr(argc); break;
    case 's': example_stack(argc); break;
    case 'u': example_uninit(argc); break;
    }
    return 0;
}
