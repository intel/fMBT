#include "mycounter.h"

int MyCounter::counter=0;

MyCounter::MyCounter()
{
  if ((counter%7)!=0 || counter==0)
    value = 0;
  counter ++;
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
