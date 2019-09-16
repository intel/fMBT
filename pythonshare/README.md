# Pythonshare

Pythonshare provides shared, persistent namespaces where Python
processes can execute and evaluate Python code.

Pythonshare is for Python 2, Python3share for Python 3.

Example: Hello world
--------------------

1. Launch a Pythonshare server in debug mode (``-d``)
   ```
   $ pythonshare-server -d
   ```

2. Run two assignments on the server, and then evaluate an expression
   through command line interface:
   ```
   $ pythonshare-client -C localhost -c 'msg1 = "hello"'
   $ pythonshare-client -C localhost -c 'msg2 = "world"'
   $ pythonshare-client -C localhost -e 'msg1 + " " + msg2 + "\n"'
   hello world
   ```

   That is, *executing* code (``-c``) does not return any value,
   *evaluating* an expression (``-e``) returns the value of the
   expression.

3. Use the same shared namespace (with ``msg1`` and ``msg2`` variables
   defined) through Python API
   ```
   $ python
   >>> import pythonshare
   >>> c = pythonshare.connect("localhost")
   >>> print c.eval_('msg1 + " " + msg2')
   hello world
   ```


Example: Debug a shell script with Pythonshare and Pycosh
---------------------------------------------------------

1. Add a "breakpoint" to a script by adding line ``pythonshare-server -d``
   ```
   $ cat myscript.sh
   #!/bin/bash
   cd /tmp
   cd foo/bar

   # Break here to see the contents of the current working directory
   pythonshare-server -d

   cat do-nothing-really.txt > /dev/null
   ```

2. Run the script. It will now stop at the "breakpoint".
   ```
   $ ./myscript
   ```

3. Get a pycosh prompt inside the pythonshare-server launched in the script.
   ```
   $ python -m pycosh
   localprompt: pspycosh localhost
   inside-the-server-prompt: [here you can do "ls", "pwd", "help", etc.]
   ```

4. Finally, kill the server to let the script continue from the
   "breakpoint":
   ```
   $ pythonshare-client -C localhost --kill
   ```
