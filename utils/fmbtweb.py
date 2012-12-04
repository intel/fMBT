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
import os

import BaseHTTPServer
import SimpleHTTPServer

# fmbtweb_js is the JavaScript module that runs on browsers and
# communicates with the fmbtweb HTTP server.

fmbtweb_js = '''
function send_to_server(response, callback) {
    url = "%(server)s/fMBTweb." + response;

    var xmlHttp = window.XMLHttpRequest ? new XMLHttpRequest() : new ActiveXObject("MSXML2.XMLHTTP.3.0");

    xmlHttp.onreadystatechange = function() {
        if (xmlHttp.readyState == 4) callback(xmlHttp);
    }
    xmlHttp.open("GET", url, true);
    xmlHttp.send();
}

function eval_response(xmlHttp) {
    try {
	eval_result = eval(xmlHttp.responseText);
    } catch (err) {
	eval_result = "fMBTweb error: " + err.description;
    }
    send_to_server(JSON.stringify(eval_result), eval_response);
}

send_to_server(null, eval_response);
'''

_defaultPage_html='''
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
''' % (fmbtweb_js,)

class JS:
    _instance = None

    def __init__(self, port=None, host="localhost", browser=None, pollDelay=0.5,
                 htmlString=_defaultPage_html, htmlFile=None):
        """Start HTTP server and optionally launch a browser that
        connects to it.

        port       - number of the port listened by the server. If port is
                     not given, a random port is used.

        host       - browser, if defined, connects to http://host:port.
                     Default host is 'localhost'.

        browser    - shell command to launch the browser (without url)
                     if not given, browser is not launched. If you need
                     to give special parameters to the browser, you can launch
                     it separately. For instance:

                     import fmbtweb
                     import subprocess
                     js = fmbtweb.JS()
                     browser = subprocess.Popen("firefox http://localhost:" +
                                                str(js.port()), shell=True)
                     js.eval("1+1")

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
            self._html = htmlString % {"server": "http://" + str(self._host) + ":" + str(self._port)}

        self.startHTTPServer()

        if browser:
            self.startBrowser(browser)
        else:
            self._browserProcess = None

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
        self._browserCommand = [browser, serverAddress]
        self._wdevnull = file(os.devnull, "w")
        self._rdevnull = file(os.devnull, "r")
        try:
            self._browserProcess = subprocess.Popen(
                self._browserCommand,
                stdin=self._rdevnull,
                stdout=self._wdevnull,
                stderr=self._wdevnull)
            if not self._browserProcess.poll() in [None, 0]:
                raise Exception('browser exited with status %s' %
                                (self._browserProcess.poll(),))
        except Exception, e:
            raise Exception('Failed to launch browser "%s":\n%s' %
                            (self._browserCommand[0], e))

    def eval(self, js, waitForResult=True):
        """Evaluates js in browser. If waitForResult == True
        (default), waits for the result and returns it as a JSON
        encoded string. If waitForResult == False, returns when js has
        been sent to the browser and returns None.
        """
        # set attributes for MyRequestHandler to send to browser
        self._toEval = js
        self._fromEval = None
        self._waitingForEval = True
        self._jsSentForEval = False
        self._waitForResult = waitForResult
        self._evalReady.acquire()
        return self._fromEval

class _fMBTwebRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def __init__(self, *args):
        SimpleHTTPServer.SimpleHTTPRequestHandler.__init__(self, *args)

    def log_request(self, *args):
        pass # don't want to log send_responses

    def log_error(self, *args):
        pass # should log errors (like 404) some day

    def send_ok(self, content, contentType = "text/html"):
        self.send_response(200)
        self.send_header("Content-type", contentType)
        self.send_header("Content-length", str(len(content)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        jsInstance = JS._instance
        if self.path == '/':
            self.send_ok(jsInstance._html)
            return
        elif self.path == '/fmbtweb.js':
            self.send_ok(fmbtweb_js % {"server": "http://" + jsInstance._host + ":" + str(jsInstance._port)}, "text/javascript")
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
                    if not jsInstance._waitForResult:
                        jsInstance._waitingForEval = False
                        jsInstance._evalReady.release()
                    return
                else:
                    # JS was already sent to the browser. Now deliver
                    # the response and release the lock.
                    jsInstance._fromEval = response
                    jsInstance._waitingForEval = False
                    jsInstance._evalReady.release()
                    self.send_ok("'fMBTweb poll'")
                    return
            time.sleep(jsInstance._pollDelay)
            self.send_ok("'fMBTweb poll'")
            return
        # Base class serves a file according to self.path
        SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)

def _run_server(server):
    try:
        server.serve_forever()
    except Exception:
        pass # log wanted someday...

def _start_http_server(port):
    server = BaseHTTPServer.HTTPServer(('', int(port)), _fMBTwebRequestHandler)
    thread.start_new_thread(_run_server,(server,))
    return server


if __name__ == '__main__':
    # This is a fMBTweb self-test
    import json

    try: browsercmd = sys.argv[1]
    except: browsercmd = 'chromium'

    verdict = 'fail'
    try:
        # Start http server and browser
        iJS = JS(browser=browsercmd)

        # Define a JavaScript function that returns an array
        iJS.eval('f = function () {return new Array("foo", "bar")}')

        # Call the function and read the return value
        result = iJS.eval('f()')

        # Convert the result to Python using json.
        if json.loads(result) == ["foo", "bar"]:
            verdict = 'pass'
            iJS.eval("divfMBTweb.innerHTML='fMBTweb self test: PASS.'")
            # Must not wait for result of window.close(), because the
            # browser might not respond anymore. This would result in
            # a deadlock.
            iJS.eval("self.close()", waitForResult=False)
        else:
            iJS.eval("divfMBTweb.innerHTML='fMBTweb self test: FAIL.'")
    finally:
        try: iJS.stop()
        except: pass
        print verdict
