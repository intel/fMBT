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

Fast mouse movement: CAPSLOCK + LEFTALT + (NUMPAD) UP/DOWN/LEFT/RIGHT
Slow mouse movement: CAPSLOCK +           (NUMPAD) UP/DOWN/LEFT/RIGHT
Left mouse button:   CAPSLOCK + NUMPAD 7 or CAPSLOCK + A
Middle mouse button: CAPSLOCK + NUMPAD 5 or CAPSLOCK + S
Right mouse button:  CAPSLOCK + NUMPAD 9 or CAPSLOCK + D

Usage: caps_and_numpad_is_mouse.py KEYBOARD_DEVICE

Example:
  sudo caps_and_numpad_is_mouse.py /dev/input/by-id/*kbd
"""

import math
import sys
import Queue
import thread
import time

import fmbtuinput  # from fMBT/utils

keymap = {
    'mouse': set(('KEY_CAPSLOCK',)),
    'mouse-fast': set(('KEY_LEFTALT',)),
    'mouse-move-up': set(('KEY_KP8', 'KEY_UP')),
    'mouse-move-down': set(('KEY_KP2', 'KEY_DOWN')),
    'mouse-move-left': set(('KEY_KP4', 'KEY_LEFT')),
    'mouse-move-right': set(('KEY_KP6', 'KEY_RIGHT')),
    'mouse-button-left': set(('KEY_KP7', 'KEY_A')),
    'mouse-button-middle': set(('KEY_KP5', 'KEY_S')),
    'mouse-button-right': set(('KEY_KP9', 'KEY_D'))
}

keymap['mouse-move'] = keymap['mouse-move-up'].union(
    keymap['mouse-move-down']).union(
    keymap['mouse-move-left']).union(
    keymap['mouse-move-right'])

keymap['mouse-button'] = keymap['mouse-button-left'].union(
    keymap['mouse-button-middle']).union(
    keymap['mouse-button-right'])

quit_lock = thread.allocate_lock()
quit_lock.acquire()

kbd_event_queue = Queue.Queue()

try:
    kbd_dev_name = sys.argv[1]
except:
    print __doc__
    sys.exit(1)

# Create new virtual mouse device
mouse = fmbtuinput.Mouse()
mouse.create()

for k in sorted(keymap.keys()):
    if k == "mouse" or k.startswith('mouse-move-') or k.startswith('mouse-button-'):
        print k, sorted(keymap[k])
print ""
print "Start reading keyboard from device", kbd_dev_name
thread.start_new_thread(
    fmbtuinput.queueEventsFromFile,
    (kbd_dev_name, kbd_event_queue, quit_lock, {"type": ["EV_KEY"]}))

def has_key(key_meaning, keys, clear=False):
    for key in keymap[key_meaning]:
        if key in keys:
            if clear:
                keys.remove(key)
            return True
    return False

def event_sender_thread():
    global event_sender_running
    mouse_y_delta = 1
    mouse_x_delta = 1
    while keys_down or keys_released:
        if has_key("mouse", keys_down):
            if has_key("mouse-fast", keys_down):
                max_speed = 30
                mouse_accel = max_speed
            else:
                max_speed = 5
                mouse_accel = max_speed
            if has_key("mouse-button-left", keys_down, clear=True):
                mouse.press("BTN_LEFT")
            if has_key("mouse-button-left", keys_released, clear=True):
                mouse.release("BTN_LEFT")
            if has_key("mouse-button-middle", keys_down, clear=True):
                mouse.press("BTN_MIDDLE")
            if has_key("mouse-button-middle", keys_released, clear=True):
                mouse.release("BTN_MIDDLE")
            if has_key("mouse-button-right", keys_down, clear=True):
                mouse.press("BTN_RIGHT")
            if has_key("mouse-button-right", keys_released, clear=True):
                mouse.release("BTN_RIGHT")
            if has_key("mouse-move-up", keys_down):
                mouse.moveRel(0, -mouse_y_delta)
                mouse_y_delta += mouse_accel
            elif has_key("mouse-move-down", keys_down):
                mouse.moveRel(0, +mouse_y_delta)
                mouse_y_delta += mouse_accel
            else:
                mouse_y_delta = 0
            if has_key("mouse-move-left", keys_down):
                mouse.moveRel(-mouse_x_delta, 0)
                mouse_x_delta += mouse_accel
            elif has_key("mouse-move-right", keys_down):
                mouse.moveRel(+mouse_x_delta, 0)
                mouse_x_delta += mouse_accel
            else:
                mouse_x_delta = 0
            if mouse_x_delta > max_speed:
                mouse_x_delta = max_speed
            if mouse_y_delta > max_speed:
                mouse_y_delta = max_speed
            if mouse_x_delta > 0 and mouse_y_delta > 0:
                alpha = math.atan(mouse_y_delta / float(mouse_x_delta))
                speed = min(max_speed, math.sqrt(mouse_x_delta**2 + mouse_y_delta**2))
                mouse_x_delta = speed * math.cos(alpha)
                mouse_y_delta = speed * math.sin(alpha)
        for key in tuple(keys_released): # clear released keys
            keys_released.remove(key)
        time.sleep(0.03)
    event_sender_running = False

code2key = {code: key for key, code in fmbtuinput.keyCodes.items()}
keys_down = set()
keys_released = set()
event_sender_running = False
while True:
    ts, tus, typ, cod, val = kbd_event_queue.get()
    key = code2key[cod]
    if val == 1:
        keys_down.add(key)
    elif val == 0:
        if key in keys_down:
            keys_down.remove(key)
        keys_released.add(key)
    if keys_down and not event_sender_running:
        event_sender_running = True
        thread.start_new_thread(event_sender_thread, ())
