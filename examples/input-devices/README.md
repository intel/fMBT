This example demonstrates using `fmbtuinput.py`. It reads keyboard
events and converts CAPSLOCK+NUMPAD events into mouse movements and
mouse button presses.

1. Create a new (virtual) input device:
   ```python
   mouse = fmbtuinput.Mouse()
   mouse.create()
   ```

2. Generate input device events:
   ```python
   mouse.press("BTN_LEFT")
   mouse.release("BTN_LEFT")
   mouse.moveRel(-10, 0)
   ```

3. Read events from an input device into a queue. This snippet uses a
   filter that take will pick only `EV_KEY` events.
   ```python
   event_queue = Queue.Queue()
   quit_lock = thread.allocate_lock()
   quit_lock.acquire()

   thread.start_new_thread(
       fmbtuinput.queueEventsFromFile,
       (input_dev_name,
        event_queue,
        quit_lock,
        {"type": ["EV_KEY"]}))
   ```
   (You can stop the queue loop with `quit_lock.release()` later on.)

4. Handle events from the queue:
   ```python
   (timestamp, timestamp_us, ev_type, ev_code, ev_value) = event_queue.get()
   if ev_code == fmbtuinput.keyCodes["KEY_CAPSLOCK"]:
       # Do what you like. ev_value 0/1/2 means release/press/repeat.
   ```

If you use this example with X server, you probably like to run
```bash
$ xmodmap ./xmodmap-capsnumpad
```

This will change X keysyms from CAPSLOCK+NUMPAD combinations into
`VoidSymbol` in order to make X11 applications pretty much ignore the
keypresses that are ment to move a mouse.

Run as root in order to read, write and create /dev/input/*. Give the
keyboard device name as the first parameter.

```bash
$ sudo python2 caps_and_numpad_is_mouse.py /dev/input/by-id/*kbd
```
