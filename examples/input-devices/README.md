This example demonstrates using `fmbtuinput.py`. It reads keyboard
events and converts CAPSLOCK+NUMPAD events into relative mouse
movements and mouse button presses.

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

3. Queue events from an input device. This snippet uses a filter that
   takes only `EV_KEY` events.
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

4. Handle events from the queue:
   ```python
   (timestamp, timestamp_us, ev_type, ev_code, ev_value) = event_queue.get()
   if ev_code == fmbtuinput.keyCodes["KEY_CAPSLOCK"]:
       ...do what you like. ev_value 0/1/2 means release/press/repeat
   ```

If you use this example with X server, you probably like to run
```bash
$ xmodmap ./xmodmap-capsnumpad
```

This will change X keycodes from CAPSLOCK+NUMPAD combinations into
`VoidSymbol` in order to let X11 applications pretty much ignore the
keypresses.
