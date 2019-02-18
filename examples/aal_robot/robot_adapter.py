from robot.api import TestSuite, ResultWriter

suite = None

def addStep(keyword, args, name):
    global suite
    if not suite:
        suite = TestSuite("Run from FMBT")
        suite.resource.imports.resource("browser.robot")
    test = suite.tests.create(name)
    if args:
        test.keywords.create(keyword, args=args.split("\t"))
    else:
        test.keywords.create(keyword)

def run():
    result = suite.run(output="robot_aal.xml")
    writer = ResultWriter(result)
    writer.write_results(report="aal_robot.html", log=None)
    return result.return_code
