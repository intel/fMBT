AUTODEBUG=../../bin/autodebug
VALGRIND_AUTODEBUG=../../bin/valgrind-autodebug

buggy: buggy.c
	gcc -O0 -g -o $@ $^
buggy-s: buggy.c
	gcc -O0 -g -fsanitize=address -fsanitize-recover=address -o $@ $^

autodebug-pointer: buggy
	$(AUTODEBUG) ./buggy p
autodebug-uninit: buggy
	$(VALGRIND_AUTODEBUG) ./buggy u
autodebug-stack: buggy-s
	$(AUTODEBUG) ./buggy-s s

check: autodebug-pointer autodebug-uninit autodebug-stack

clean:
	$(RM) buggy buggy-s *~
