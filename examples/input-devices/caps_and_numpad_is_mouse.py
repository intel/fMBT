#!/usr/bin/env python2
#
# Copyright 2020 Antti Kervinen <antti.kervinen@gmail.com>
#
# License (MIT):
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Generate mouse events from CAPSLOCK + NUMPAD

Events are sent through new virtual mouse input device. (No physical
mouse needed in the system.)

Fast mouse movement: CAPSLOCK + LEFTALT + NUMPAD UP/DOWN/LEFT/RIGHT
Slow mouse movement: CAPSLOCK +           NUMPAD UP/DOWN/LEFT/RIGHT
Left mouse button:   CAPSLOCK + NUMPAD 7
Middle mouse button: CAPSLOCK + NUMPAD 5
Right mouse button:  CAPSLOCK + NUMPAD 9

Disable CAPSLOCK + NUMPAD symbols with .Xmodmap:
(This makes CAPSLOCK a modifier, SHIFT+CAPSLOCK will be the old CAPSLOCK.)

remove Lock = Caps_Lock
keycode 66 = Mode_switch Caps_Lock
keycode 79 = KP_Home KP_7 VoidSymbol VoidSymbol VoidSymbol VoidSymbol
keycode 80 = KP_Up KP_8 VoidSymbol VoidSymbol VoidSymbol VoidSymbol
keycode 81 = KP_Prior KP_9 VoidSymbol VoidSymbol VoidSymbol VoidSymbol
keycode 83 = KP_Left KP_4 VoidSymbol VoidSymbol VoidSymbol VoidSymbol
keycode 84 = KP_Begin KP_5 VoidSymbol VoidSymbol VoidSymbol VoidSymbol
keycode 85 = KP_Right KP_6 VoidSymbol VoidSymbol VoidSymbol VoidSymbol
keycode 88 = KP_Down KP_2 VoidSymbol VoidSymbol VoidSymbol VoidSymbol

"""

import glob
import Queue
import thread
import time

import fmbtuinput  # from fMBT/utils

quit_lock = thread.allocate_lock()
quit_lock.acquire()

kbd_event_queue = Queue.Queue()

kbd_dev_name = glob.glob("/dev/input/by-id/*-kbd")[0]

# Create new virtual mouse device
mouse = fmbtuinput.Mouse()
mouse.create()

print "start reading keyboard from device", kbd_dev_name
thread.start_new_thread(
    fmbtuinput.queueEventsFromFile,
    (kbd_dev_name, kbd_event_queue, quit_lock, {"type": ["EV_KEY"]}))

def event_sender_thread():
    global event_sender_running
    mouse_y_delta = 1
    mouse_x_delta = 1
    while keys_down:
        if "KEY_CAPSLOCK" in keys_down:
            if "KEY_LEFTALT" in keys_down:
                max_speed = 30
                mouse_accel = 10
            else:
                max_speed = 5
                mouse_accel = 1
            if "KEY_KP7" in keys_down:
                keys_down.remove("KEY_KP7") # one-shot key
                mouse.press("BTN_LEFT")
                mouse.release("BTN_LEFT")
            if "KEY_KP5" in keys_down:
                keys_down.remove("KEY_KP5") # one-shot key
                mouse.press("BTN_MIDDLE")
                mouse.release("BTN_MIDDLE")
            if "KEY_KP9" in keys_down:
                keys_down.remove("KEY_KP9") # one-shot key
                mouse.press("BTN_RIGHT")
                mouse.release("BTN_RIGHT")
            if "KEY_KP8" in keys_down:
                mouse.moveRel(0, -mouse_y_delta)
                mouse_y_delta += mouse_accel
            if "KEY_KP2" in keys_down:
                mouse.moveRel(0, +mouse_y_delta)
                mouse_y_delta += mouse_accel
            if "KEY_KP4" in keys_down:
                mouse.moveRel(-mouse_x_delta, 0)
                mouse_x_delta += mouse_accel
            if "KEY_KP6" in keys_down:
                mouse.moveRel(+mouse_x_delta, 0)
                mouse_x_delta += mouse_accel
            if not ("KEY_KP8" in keys_down or
                    "KEY_KP2" in keys_down or
                    "KEY_KP4" in keys_down or
                    "KEY_KP6" in keys_down):
                mouse_y_delta = 1
                mouse_x_delta = 1
            if mouse_x_delta > max_speed:
                mouse_x_delta = max_speed
            if mouse_y_delta > max_speed:
                mouse_y_delta = max_speed
        time.sleep(0.03)
    event_sender_running = False

code2key = {code: key for key, code in fmbtuinput.keyCodes.items()}
keys_down = set()
event_sender_running = False
while True:
    ts, tus, typ, cod, val = kbd_event_queue.get()
    key = code2key[cod]
    if val == 1:
        keys_down.add(key)
    elif val == 0 and key in keys_down:
        keys_down.remove(key)
    if keys_down and not event_sender_running:
        event_sender_running = True
        thread.start_new_thread(event_sender_thread, ())
