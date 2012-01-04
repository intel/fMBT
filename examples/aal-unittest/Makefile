CXXFLAGS := -O0 -g -Wall -pedantic -I../../src -I/usr/include/fmbt -fPIC

# Enable building a faulty implementation of mycounter with "make
# FAULTY=1" command. Faulty mycounter.cc does not initialise counter
# value in its constructor.
ifdef FAULTY
CXXFLAGS += -DFAULTY
endif

# Rule for running the test, that is, producing the log file. Because
# fmbt exits with an error value in case the test fails, we use
# "... || true" to suppress Make error message.
mycountertest.log: mycountertest.conf mycountertest.so
	fmbt -l$@ $< || true

# Link the unit under test and test steps into a shared library. Make
# is smart enough to compile mycounter.cc and mycountertest.cc to
# produce the required object files.
mycountertest.so: mycounter.o mycountertest.o
	$(CXX) -shared -o $@ $^

# Generic rule for generating C++ from AAL. When make notices that it
# needs mycountertest.cc due to the linking rule, this rules tells how
# to create it from mycountertest.cc.aal. PRECIOUS prevents deleting
# the .cc file automatically. That's nice in case you need gdb, for
# instance.
%PRECIOUS: %.cc
%.cc: %.cc.aal
	fmbt-aalc -o $@ $<

clean:
	$(RM) *.o *.so mycountertest.cc mycountertest.log
