#!/usr/bin/env python

# fMBT, free Model Based Testing tool
# Copyright (c) 2011, Intel Corporation.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU Lesser General Public License,
# version 2.1, as published by the Free Software Foundation.
#
# This program is distributed in the hope it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for
# more details.
#
# You should have received a copy of the GNU Lesser General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin St - Fifth Floor, Boston, MA 02110-1301 USA.

"""
Browser/Javascript test driver for fMBT

Example:

iJS = fmbtweb.JS(port=5555, browser='chromium', htmlFile='my.html')

This starts new HTTP server at localhost's port 5555. Then launches
Chromium and connects it to http://localhost:5555. The default page
the server serves is my.html. Note that the page must include
fmbtweb.js.

Define a JavaScript function:

iJS.eval('foo = function() { return 42; }')

Call the function:

result = iJS.eval('foo()')

Use json to convert the result to corresponding Python type

import json
if json.loads(result) == 42: print "success"
"""

import random
import subprocess
import sys
import thread
import threading
import time
import urllib

import BaseHTTPServer
import SimpleHTTPServer

_html_basepage='''
<html>
    <head>
        <script language="JavaScript" type="text/javascript">
        %s
        </script>
    </head>
    <body>
        <div id="divfMBTweb">
        fMBTweb
        </div>
    </body>
</html>
''' % (file("fmbtweb.js").read(),)

class JS:
    _instance = None

    def __init__(self, port=None, host="localhost", browser=None, pollDelay=0.5,
                 htmlString=_html_basepage, htmlFile=None):
        """Start HTTP server and optionally launch a browser that
        connects to it.

        port       - number of the port listened by the server. If port is
                     not given, a random port is used.

        host       - browser, if defined, connects to http://host:port.
                     Default host is 'localhost'.

        browser    - shell command to launch the browser (without url)

        pollDelay  - max delay between polling new javascript to be
                     evaluated.

        htmlString - html of the default page to be served to the browser

        htmlFile   - html of the default page is read from the this file.
                     The file must include fmbtweb.js script!
        """
        if port == None: self._port = random.randint(10000,50000)
        else: self._port = port
        self._host = host

        if htmlFile:
            self._html = file(htmlFile).read()
        elif htmlString:
            self._html = htmlString

        self.startHTTPServer()

        if browser:
            self.startBrowser(browser)

        JS._instance = self

        self._waitingForEval = False
        self._evalReady = threading.Lock()
        self._evalReady.acquire()

        self._pollDelay = pollDelay

    def port(self):
        "returns the port at which the HTTP server is running"
        return self._port

    def stop(self):
        self.stopHTTPServer()
        if self._browserProcess:
            self._browserProcess.terminate()

    def startHTTPServer(self):
        self._server = _start_http_server(self._port)

    def stopHTTPServer(self):
        self._server.shutdown()

    def startBrowser(self, browser):
        serverAddress = "http://%s:%s" % (self._host, self._port)
        self._browserCommand = (browser + " " + serverAddress
                                + ">/dev/null 2>&1")
        self._browserProcess = subprocess.Popen(
            self._browserCommand,
            shell=True,
            stdin=None, stdout=None, stderr=None)

    def eval(self, js):
        # send attributes for MyRequestHandler to send to browser
        self._toEval = js
        self._fromEval = None
        self._waitingForEval = True
        self._jsSentForEval = False
        # wait for the result
        self._evalReady.acquire()
        response = self._fromEval
        return response

class _MyRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def __init__(self, *args):
        SimpleHTTPServer.SimpleHTTPRequestHandler.__init__(self, *args)

    def log_request(self, *args):
        pass # don't want to log send_responses

    def log_error(self, *args):
        pass # should log errors (like 404) some day

    def send_ok(self, content):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        jsInstance = JS._instance
        if self.path == '/':
            self.send_ok(jsInstance._html)
            return
        elif self.path.startswith('/fMBTweb.'):
            response = urllib.unquote(self.path[9:])
            jsInstance = JS._instance
            if jsInstance._waitingForEval:
                if not jsInstance._jsSentForEval:
                    # This request is not yet handled.
                    # Send JS now to the browser and mark the
                    # request being sent (_fromEval value).
                    jsInstance._jsSentForEval = True
                    self.send_ok(jsInstance._toEval)
                    return
                else:
                    # JS was already sent to the browser. Now deliver
                    # the response and release the lock.
                    jsInstance._fromEval = response
                    jsInstance._waitingForEval = False
                    jsInstance._evalReady.release()
                    return
            time.sleep(jsInstance._pollDelay)
            self.send_ok("'fMBTweb poll'")
            return
        SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)

def _run_server(server):
    try:
        server.serve_forever()
    except Exception:
        pass # log wanted someday...

def _start_http_server(port):
    server = BaseHTTPServer.HTTPServer(('', int(port)), _MyRequestHandler)
    thread.start_new_thread(_run_server,(server,))
    return server


if __name__ == '__main__':
    # This is a fMBTweb self-test
    import json

    try: browsercmd = sys.argv[1]
    except: browsercmd = 'chromium'

    verdict = 'fail'
    try:
        # Start http server and " + browsercmd
        iJS = JS(browser=browsercmd)

        # Define a JavaScript function that returns an array"
        iJS.eval('f = function () {return new Array("foo", "bar");};')

        # Call the function and read the return value
        result = iJS.eval('f()')

        # Convert the result to Python using json.
        if json.loads(result) == ["foo", "bar"]:
            verdict = 'pass'
            iJS.eval("divfMBTweb.innerHTML='fMBTweb self test: PASS.';")
        else:
            iJS.eval("divfMBTweb.innerHTML='fMBTweb self test: FAIL.';")
    finally:
        try: iJS.stop()
        except: pass
        print verdict
