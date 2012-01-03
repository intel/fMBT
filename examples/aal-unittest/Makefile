CXXFLAGS=-O0 -g -Wall -pedantic -I../../src -I/usr/include/fmbt

ifdef FAULTY
CXXFLAGS += -DFAULTY
endif

mycountertest.log: mycountertest.conf mycountertest.so
	fmbt -l$@ $< || true

mycountertest.so: mycounter.o mycountertest.cc
	g++ $(CXXFLAGS) $^ -shared -fPIC -o $@

%.cc: %.aal
	fmbt-aalc -o $@ $<

clean:
	$(RM) *.o *.so mycountertest.cc mycountertest.log
