CXXFLAGS := -O2 -g -Wall -pedantic -I../../src -I/usr/include/fmbt -fPIC

# Enable building a faulty implementation of mycounter with "make
# FAULTY=1" command. Faulty mycounter.cc does not initialise counter
# value in its constructor.
CXXFLAGS += -DFAULTY
LOGFILE=shortener.log
fail.log: test.log
	$(RM) pass
	./shortener.sh test.conf test.log >> ${LOGFILE} 2>&1 # should run 178 rounds and find error trace with 24 steps
	cp fail.log fail_pass1.log # Let's try to get an even shorter trace
# should find it in the 2nd round. It is the minimal.
	./shortener.sh test.conf fail_pass1.log  >> ${LOGFILE} 2>&1
# So. It will take 180 rounds to get the minimal error trace.
# Shortening the error trace is taking on my dev machine about 2½mins

# Rule for running the test, that is, producing the log file.
# fmbt exits with an error value in case the test fails, we use
# "... || true" to suppress Make error message.
test.log: test.conf mycountertest.so
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
.PRECIOUS: %.cc
%.cc: %.cc.aal
	fmbt-aalc -o $@ $<

clean:
	$(RM) *.o *.so mycountertest.cc test.log pass fail fail.log shortener.log fail_pass1.log
