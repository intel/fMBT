This example demonstrates how to test a JavaScript API.

The JavaScript API to be tested is in "mycounter.js".

We used the following recipe to create tests for it:

1. Create an html page that includes the API and fmbtweb.js. See
   "test.html".

2. Define test steps in "teststeps.py". When imported, this library
   establishes the connection to the browser that runs the JavaScript,
   and defines to use the "test.html" as a starting page.

3. Define (all possible) orders in which the test steps can be
   run. This is done in "testmodel.gt".

4. Create a configuration file for the test. We did two of them:
   "smoketest.conf" and "regressiontest.conf".

Then run the smoke test as follows:

$ fmbt -l smoketest.log smoketest.conf

...and the regression test as follows:

$ fmbt -l regressiontest.log regressiontest.conf

The smoke test may pass, because finding the error in mycounter.js
requires calling reset() before testing the count(). On the other
hand, if recreated between reset() and count(), the error is not
found. Thus it is easy to run every test step at least once without
finding the error.

The regression test will fail, because it aims to cover all
permutations of any two actions. These permutations include pair
<reset(), count()> among others.
