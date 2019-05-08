### Online tests for pythonshare
###
### Copyright Jukka Laukkanen / Dashing Test Automation
### jukka@dashing.fi
###

import os
import sys
import pythonshare

HUB_CONNSPEC = os.getenv("HUB_CONNSPEC", "xyz@localhost")
HUB_NS = os.getenv("HUB_NS", "logger")
TEST_ENV = os.getenv("TEST_ENV", "na")

password = HUB_CONNSPEC.split("@")[0]

# don't catch the exception, all failures needs to fail the test
print "Trying to connect to %s/%s" % (HUB_CONNSPEC, HUB_NS)
hub = pythonshare.connect(HUB_CONNSPEC, password, HUB_NS)
data_in = "data = '%s'" % (TEST_ENV,)
print "writing to hub: %s" % (data_in,)
hub.exec_in(HUB_NS, data_in)
print "reading value of 'data' from hub"
ret = hub.eval_in(HUB_NS, "data")
print "value read from hub: %s" % (ret,)
assert ret == TEST_ENV
print "Great success"