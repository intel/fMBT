.PHONY: all
all: testfalse.log testtrue.log
# Faulty MyCounter.java does not initialise counter
# value in its constructor.

# Rule for running the test, that is, producing the log file.
# fmbt exits with an error value in case the test fails, we use
# "... || true" to suppress Make error message.
test%.log: test%.conf mycountertest%.class MyCounter.class
	fmbt -l$@ $< || true

%.class: %.java
	javac $(filter %.java,$^)

# Generic rule for generating java from AAL. When make notices that it
# needs mycountertest[true|false].java, this rules tells how
# to create it from mycountertest[true|false].java.aal. PRECIOUS prevents deleting
# the .java and .class file automatically.

.PRECIOUS: %.java %.class
%.java: %.java.aal
	fmbt-aalc -o $@ $<

clean:
	$(RM) *.class mycountertest*.java test*.log
