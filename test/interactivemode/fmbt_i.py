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

import pexpect
import subprocess
import time
import types
import os
import signal

FMBT_BINARY = '../../src/fmbt'

# Fmbt instances started during tests write their log to FMBT_LOGFILE
FMBT_LOGFILE = '/tmp/fmbt.test.interactivemode.subfmbt.log'

# If an assertion fails, compared value is most often saved to the
# debug file
TEST_DEBUGFILE ='/tmp/fmbt.test.interactivemode.debug'

# Writes from started fmbt instances are redirected to FMBT_STDERRFILE
FMBT_STDERRFILE = '/tmp/fmbt.test.interactivemode.subfmbt.stderr'

PROMPT = 'fMBT> '

process_response_time = lambda: time.sleep(0.5)
ui_response_time = lambda: time.sleep(0.1)
all_actions = []

def _debug(x):
    file(TEST_DEBUGFILE,'a').write(str(x) + '\n\n')
    return x

def _output2list(ttyoutput):
    s = ttyoutput.replace('\r', '')
    return s.split('\n')

def _run_command(cmd, delay_before_output = ui_response_time):
    fmbt.write(cmd + '\n')
    delay_before_output()
    output = fmbt_output()[1:]
    _debug("command: '%s'\nresult:%s\n" % (cmd, output))
    return output

# Fmbt-i.mrules expects functions corresponding to actions to return
# True when executed successfully. On error they should return
# something - or throw an exception - that helps debugging the error.

def iStartGoodFmbt():
    global fmbt
    global fmbt_output
    fmbt = pexpect.spawn(FMBT_BINARY + ' -L' + FMBT_LOGFILE
                         + ' -i test.conf')
    def output_reader():
        s = ""
        while 1:
            try: s += fmbt.read_nonblocking(4096, 0.5)
            except pexpect.TIMEOUT: break
            except pexpect.EOF: break
        return _output2list(s)

    fmbt_output = output_reader
    process_response_time()
    output=fmbt_output()
    _debug(output)
    return output[-1] == PROMPT

def iReadAllActionsInAdapter():
    global fmbt
    global all_actions
    p = subprocess.Popen(FMBT_BINARY + ' -i -E test.conf >preprocessed.txt 2>&1', shell=True)
    process_response_time()
    assert _debug(p.poll())==0, "Incorrect fmbt exit value or fmbt not exited"

    toplevel_adapter_lines=0
    for line in file("preprocessed.txt"):
        if toplevel_adapter_lines == 0 and 'import fmbt_i' in line and '"init"' in line:
            toplevel_adapter_lines = 1
        if toplevel_adapter_lines == 1:
            if line=='"\n': break
            all_actions.append(line.split('"')[1])

    action_functions=[f for f in dir()
                      if f.startswith('i') and type(globals()[f]) == types.FunctionType]
    _debug(all_actions)
    for f in action_functions:
        assert f in all_actions, "Action '%s' not in -E output." % (f,)
    return True

def iQuit():
    _run_command('q', process_response_time)
    _debug('reading ' + FMBT_LOGFILE)
    last_log_line = file(FMBT_LOGFILE).readlines()[-1].strip()
    assert _debug(last_log_line) == '</fmbt_log>', "Log unfinished (%s)" % (last_log_line,)
    assert _debug(fmbt.isalive()) == False, "Process still alive"
    os.remove(FMBT_LOGFILE)
    return True

def iTerminate():
    os.kill(fmbt.pid, signal.SIGTERM)
    process_response_time()
    return fmbt.isalive() == False

def _validateHelp(help_lines):
    _debug(help_lines)
    assert help_lines[0].startswith('Execute actions:'), "'Execute actions' expected"
    assert help_lines[-2].startswith('Unknown command'), "'Unknown command' expected"
    assert help_lines[-1] == PROMPT, "Prompt missing"
    return True

def iHelpEmptyCommand():
    output = _run_command('')
    return _validateHelp(output)

def iHelpUnknownCommand():
    output = _run_command('?')
    return _validateHelp(output)

##########################################
# Execute actions at current state

def _find_action_cmd(list_cmd, action):
    """
    return the command which executes the action from the list that is
    printed using list_cmd.
    """
    action_cmd = ''
    for row in _run_command(list_cmd):
        if action in row:
            action_cmd = row.split(':')[0]
            break
    assert action_cmd != '', "Action '%s' not found in output of '%s'" % (action, list_cmd)
    return action_cmd

def _validateExecOutput(output, executedAction, adapterResult, modelResult, nextActions = []):
    expected_output = ["executing: " + executedAction,
                       "adapter:   " + adapterResult,
                       "model:     " + modelResult]
    expected_output.extend(nextActions)
    expected_output.append(PROMPT)
    _debug('observed: ' + str(output) + '\nrequired: ' + str(expected_output))
    assert output == expected_output, "Validating exec result failed."

def iListActionsAtState():
    output = _run_command('s')
    return output[0].startswith('s1:')

def iListActionsAtAdapter():
    output = _run_command('e')
    return output[0].startswith('e1:')

def iExecuteInitAtState():
    _run_command('oea1')
    _run_command('oem1')
    output = _run_command(_find_action_cmd('s', 'init'))
    _validateExecOutput(output, "init", "init", "ok", ["s1:iReadAllActionsInAdapter"])
    return True

def iExecuteInitAtStateExecModel():
    _run_command('oea0')
    _run_command('oem1')
    output = _run_command('s' + _find_action_cmd('s', 'init')[1:])
    _validateExecOutput(output, "init", "[skipped]", "ok", ["s1:iReadAllActionsInAdapter"])
    return True

def iExecuteReadAllAtState():
    _run_command('oea0')
    _run_command('oem1')
    output = _run_command('s' + _find_action_cmd('s', 'iReadAllActionsInAdapter')[1:])
    _validateExecOutput(output, "iReadAllActionsInAdapter", "[skipped]", "ok",
                        ["s1:iStartGoodFmbt"])
    return True

##########################################
# Execute actions at top-level adapter

def iExecuteInitAtAdapter():
    _run_command('oea1')
    _run_command('oem0')
    output = _run_command(_find_action_cmd('e', 'init'))
    _validateExecOutput(output, "init", "init", "[skipped]")
    return True

def iExecuteInitAtAdapterByName():
    _run_command('oea1')
    _run_command('oem0')
    output = _run_command('init')
    _validateExecOutput(output, "init", "init", "[skipped]")
    return True

def iExecuteInitAtAdapterExecModel():
    _run_command('oea0')
    _run_command('oem1')
    output = _run_command('e' + _find_action_cmd('e', 'init')[1:])
    _validateExecOutput(output, "init", "[skipped]", "ok")
    return True
