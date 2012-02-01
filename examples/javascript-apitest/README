This example demonstrates how to test a JavaScript API.

The JavaScript module to be tested is in "mycounter.js".

We used the following recipe to create tests for it:

1. Create an html page that includes the API and fmbtweb.js. See
   "test.html".

2. Define test steps in a Python library. We did this in
   "teststeps.py". This library contains one function per step. When
   imported the library connects to the browser that will run the
   JavaScript. We used Firefox in this example. "test.html" is sent to
   the browser as a starting page.

3. Define orders in which the test steps can be executed. We used a
   state machine to do this, see "testmodel.gt".

4. Create a configuration file for the test. We did three of them:
   "smoketest.conf", "regressiontest.conf", "reliabilitytest.conf"

Then run the smoke test as follows:

$ fmbt -l smoketest.log smoketest.conf

the regression test as follows:

$ fmbt -l regressiontest.log regressiontest.conf

...and the reliability test as follows:

$ fmbt -l reliabilitytest.log reliabilitytest.conf

The JavaScript module contains an bug: reset() does not work if the
counter value is zero when reset() is called.

The smoke test may still pass, because detecting the bug requires
first calling reset() when the internal value is zero, and calling
count() after that. On the other hand, if mycounter instance becomes
destroyed and reinstantiated between the broken reset() and count(),
the error will not be found. Thus it is easy to run through every test
step without finding the bug. Smoke test stops when every test step
has been executed at least once.

The regression test is likely to fail, because it aims to cover all
permutations of any two actions. It will test <reset(), reset()> and
<new mycounter(0), reset()>, for instance. Both of these will set
not-a-number to counter's value attribute. If the test generator
happens to test <reset(), count()> after this kind of reset, the bug
will be detected.

The reliability test will always fail. The test generator tries to
cover all permutations of any three actions. This means that sequence
<reset(), reset(), count()> will be tested, for instance. That
sequence will never pass the test, because the second reset() will
always break the value attribute, if it was not already broken.

You can find reasons for failed tests from test and adapter log
files. For instance, see reliabilitytest_adapter.log.
