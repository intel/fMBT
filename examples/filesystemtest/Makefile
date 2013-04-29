CXXFLAGS := -O0 -g -Wall -pedantic -I../../src -I/usr/include/fmbt -fPIC

all: filesystemtest.so

# Link the unit under test and test steps into a shared library.
%.so: %.o
	$(CXX) -g -shared -o $@ $^

# Generic rule for generating C++ from AAL. When make notices that it
# needs mycountertest.cc due to the linking rule, this rules tells how
# to create it from mycountertest.cc.aal. PRECIOUS prevents deleting
# the .cc file automatically. That's nice in case you need gdb, for
# instance.
.PRECIOUS: %.cc
%.cc: %.cc.aal
	fmbt-aalc -o $@ $<

clean:
	$(RM) *.o *.so
