#!/usr/bin/env python

import sys

def log(msg):
    file("/tmp/remote_model.py","a").write(msg + "\n")

log("*** remote_model.py started")

def put(msg):
    log("sending: '%s'" % (msg,))
    sys.stdout.write(str(msg) + "\n")
    sys.stdout.flush()

def put_list(list_of_integers):
    sys.stdout.write(" ".join([str(i) for i in list_of_integers]) + "\n")
    sys.stdout.flush()

def get():
    cmd = sys.stdin.readline()
    log("got command: '%s'" % (cmd,))
    return cmd

class RemoteModelBridge:
    def __init__(self, localModel):
        self._model = localModel

    def communicate(self):
        # send all action names
        action_names = self._model.getActionNames()
        put(len(action_names))
        for name in action_names:
            put(name)

        # send all state tags
        tag_names = self._model.getSPNames()
        put(len(tag_names))
        for name in tag_names:
            put(name)

        # protocol loop
        cmd = get().rstrip()
        while cmd != "":
            if cmd == "a":
                put_list(self._model.getActions())
            elif cmd == "i":
                put_list(self._model.getIActions())
            elif cmd == "p":
                put_list(self._model.getprops())
            elif cmd == "r":
                try:    self._model.reset()
                except: put(0)
                else:   put(1)
            elif cmd == "u":
                self._model.push()
            elif cmd == "o":
                self._model.pop()
            else:
                action_number = int(cmd)
                try:    self._model.model_execute(action_number)
                except: put(0)
                else:   put(action_number)
            cmd = get().rstrip()

import mytest
m = mytest.Model()
b = RemoteModelBridge(m)
b.communicate()
