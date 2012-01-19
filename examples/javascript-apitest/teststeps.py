import fmbtweb
import json

js = fmbtweb.JS(browser='firefox', htmlFile="test.html", pollDelay=0)

_expectedCounterValue = 0

def iCreate():
    # Test instantiating mycounter with zero as initial value
    global _expectedCounterValue
    js.eval('mc = new mycounter(0)', waitForResult=False)
    _expectedCounterValue = 0

def iCreate42():
    # Test instantiating mycounter with a non-zero initial value
    global _expectedCounterValue
    js.eval('mc = new mycounter(42)', waitForResult=False)
    _expectedCounterValue = 42

def iDestroy():
    js.eval('mc = null', waitForResult=False)

def iTestInc():
    global _expectedCounterValue
    js.eval('mc.inc()', waitForResult=False)
    _expectedCounterValue += 1

def iTestReset():
    global _expectedCounterValue
    js.eval('mc.reset()', waitForResult=False)
    _expectedCounterValue = 0

def iTestCount():
    global _expectedCounterValue
    result = js.eval('mc.count()')
    if not json.loads(result) == _expectedCounterValue:
        raise Exception("Expected value: %s, observed result: %s"
                        % (_expectedCounterValue, result))
