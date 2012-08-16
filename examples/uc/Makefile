
all:	out.html

out.html: ../c++-unittest/test.log test.uc
	LD_LIBRARY_PATH=../c++-unittest/ ../../src/fmbt-ucheck -u test.uc -f html -o out.html ../c++-unittest/test.log


../c++-unittest/test.log:
	make -C ../c++-unittest test.log

