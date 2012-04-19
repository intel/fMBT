#ifndef __mycounter_h__
#define __mycounter_h__

class MyCounter {
public:
    MyCounter();
    void inc();
    void reset();
    int count();
private:
    int value;
    static int counter;
};

#endif
