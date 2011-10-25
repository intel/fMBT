
all:
	swig  -python -external-runtime
	swig  -python dparser.i
	python setup.py build
	echo "type 'sudo make install' to install"

install:
	python setup.py install

clean:
	rm -rf build dparser.pyc dparser_swigc.* dparser_wrap.c swigpyrun.h tests/d_parser_mach_gen.*

test:
	python tests/test.py
	python tests/test2.py
	python tests/test3.py
	python tests/test4.py
	python tests/test5.py
	python tests/test6.py
	python tests/test7.py
