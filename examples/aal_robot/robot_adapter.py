from robot.api import TestSuite, ResultWriter

suite = None
test = None
robotfile = []

def addTestSuite(name):
    """ Initialize Robot test suite object """
    global suite
    suite = TestSuite("name")
    suite.resource.imports.resource("browser.robot")

    robotfile.append("*** Generated from fMBT ***")
    robotfile.append("*** Settings ***")
    robotfile.append("Resource  browser.robot")
    robotfile.append("")
    robotfile.append("*** Test Cases ***")

def addTestCase(name):
    """ Add testcase to robot suite.tests object and robot file """
    global test
    test = suite.tests.create(name)
    robotfile.append("\n" + name)

def addStep(keyword, args, name):
    """ Add test step to robot test object and robot file"""
    if args:
        test.keywords.create(keyword, args=args.split("\t"))
        robotfile.append("  " + keyword + "  " + args.replace("\t", "  "))
    else:
        test.keywords.create(keyword)
        robotfile.append("  " + keyword)

def run():
    """ Run generated test case.
    Write generated test case to robot file """

    with open("robotfile.robot", "w") as testsuite:
        testsuite.write("\n".join(robotfile))
        testsuite.write("\n")
    result = suite.run(output="robot_aal.xml")
    writer = ResultWriter(result)
    writer.write_results(report="aal_robot.html", log=None)
    return result.return_code
