#include "mycounter.h"

MyCounter::MyCounter()
{
#ifndef FAULTY
    value = 0;
#endif
}

void MyCounter::inc() {
    value += 1;
}

void MyCounter::reset() {
    value = 0;
}

int MyCounter::count() {
    return value;
}
