import copy
import types
import time
import traceback
import fmbt

SILENCE = -3

_g_immutable_types = set(
    [str, int, int, float, bool, type(None), tuple])

def setCodeFileLine(c, filename, lineno, funcname=None):
    if funcname == None:
        funcname = c.co_name
    if hasattr(c, 'co_posonlyargcount'): # Python 3.8 onwards
        rv = types.CodeType(
            c.co_argcount, c.co_posonlyargcount, c.co_kwonlyargcount,
            c.co_nlocals, c.co_stacksize, c.co_flags,
            c.co_code, c.co_consts, c.co_names, c.co_varnames,
            filename, funcname, lineno, c.co_lnotab, c.co_freevars)
    else: # Python 3.7 and earlier
        rv = types.CodeType(
            c.co_argcount, c.co_kwonlyargcount,
            c.co_nlocals, c.co_stacksize, c.co_flags,
            c.co_code, c.co_consts, c.co_names, c.co_varnames,
            filename, funcname, lineno, c.co_lnotab, c.co_freevars)
    return rv

class AALModel:
    def __init__(self, model_globals):
        self._aal_block_name = {} # guard|body|adapter name -> tag/action name
        self._all_guards = self._get_all("guard", "action")
        self._all_bodies = self._get_all("body", "action")
        self._all_adapters = self._get_all("adapter", "action")
        self._all_names = self._get_all("name", "action")
        self._all_types = self._get_all("type", "action")
        self._all_tagnames = self._get_all("name", "tag")
        self._all_tagguards = self._get_all("guard", "tag")
        self._all_tagadapters = self._get_all("adapter", "tag")
        if len(self._get_all("guard_next_block", "serial")) > 0:
            self._has_serial = True
        else:
            self._has_serial = False
        self._variables = model_globals
        self._variables['action'] = lambda name: self._all_names.index(name) + 1
        self._variables['output'] = lambda name: self._all_names.index("o:" + name) + 1
        self._variables['input'] = lambda name: self._all_names.index("i:" + name) + 1
        self._variables['name'] = lambda name: self._all_names.index(name)
        self._variables['variable'] = lambda varname: self._variables[varname]
        self._variables['assign'] = lambda varname, v: self._variables.__setitem__(varname, v)
        self._variables['guard_list'] = []
        self._stack = []
        self._stack_executed_actions = []
        self._adapter_exit_executed = False
        self._enabled_actions_stack = [set()]
        fmbt._g_testStep = 0

    def _get_all(self, property_name, itemtype):
        plist = []
        i = 1
        while 1:
            try:
                obj = getattr(self, itemtype + str(i) + property_name)
                if (property_name in ["guard", "body", "adapter"] and
                    itemtype in ["action", "tag"]):
                    self._aal_block_name[itemtype + str(i) + property_name] \
                        = getattr(self, itemtype + str(i) + "name")
                elif itemtype == "serial":
                    self._aal_block_name["serial" + str(i) + "guard"] \
                        = getattr(self, "serial" + str(i) + "name")

                plist.append(obj)
            except: return plist
            i += 1

    def _set_all_class(self, property_name, itemtype, value_array):
        i = 1
        cls = self.__class__
        while 1:
            itemname = itemtype + str(i) + property_name
            if hasattr(cls, itemname):
                setattr(cls, itemname, value_array[i-1])
            else:
                return
            i += 1

    def call(self, func, call_arguments=None):
        guard_list = None
        try:
            fmbt._g_simulated_actions = self._stack_executed_actions
            func_name = func.__name__
            if func_name[-1] == "d": # faster than func_name.endswith("guard")
                guard_list = self._variables['guard_list']
                guard_list.append(self._aal_block_name[func_name])
                for prerequisite in func.requires:
                    if not self.call(getattr(self, prerequisite)):
                        return False
            if call_arguments:
                args = []
                for arg in call_arguments:
                    if arg == '':
                        args.append('')
                    else:
                        args.append(eval(arg, self._variables))
                self._variables['args'] = args
            else:
                self._variables['args'] = []
            rv = eval(func.__code__, self._variables)
            if guard_list:
                guard_list.pop()
            return rv
        except Exception as e:
            self._log("Exception %s in %s: %s" % (e.__class__, func.__name__, e))
            self._log(traceback.format_exc())
            if guard_list:
                guard_list.pop()
            raise

    def call_exception_handler(self, handler_name, action_name, exc, pass_through_rv=[]):
        rv = self._variables[handler_name](action_name, exc)
        if rv in pass_through_rv:
            return rv
        elif type(rv) == int:
            return rv
        elif rv == None or rv == True:
            return self._variables['action'](action_name)
        else:
            raise Exception('''Exception handler "%s('%s', %s)" returned unexpected value: %s''' %
                            (handler_name, action_name, exc, rv))

    def call_tagexception_handler(self, handler_name, tag_name, exc):
        rv = self._variables[handler_name](tag_name, exc)
        if type(rv) in [bool, types.NoneType]:
            return rv
        else:
            raise Exception('''Exception handler "%s('%s', %s)" returned unexpected value: %s''' %
                            (handler_name, tag_name, exc, rv))

    def reset(self):
        # initialize model
        fmbt._g_actionName = "AAL: initial_state"
        rv = self.call(self.initial_state)
        self._push_variables = [
            v for v in self.__class__.push_variables_set
            if (v in self._variables and
                type(eval(v, self._variables)) not in [
                    types.ModuleType, type] and
                not eval(v, self._variables) in [self])
        ]
        return rv

    def adapter_init():
        return True

    def init(self):
        # initialize adapter
        fmbt._g_actionName = "AAL: adapter_init"
        rv = self.call(self.adapter_init)
        return rv

    def adapter_exit(verdict, reason):
        return

    def aexit(self, verdict, reason):
        if not self._adapter_exit_executed:
            self._adapter_exit_executed = True
            fmbt._g_actionName = "AAL: adapter_exit"
            self.adapter_exit.__func__(verdict, reason)

    def adapter_execute(self, i, adapter_call_arguments = ()):
        if not 0 < i <= len(self._all_names):
            raise IndexError('Cannot execute action %s adapter code' % (i,))
        if self._all_types[i-1] == "input":
            try:
                fmbt._g_testStep += 1
                fmbt._g_actionName = self._all_names[i-1]
                rv = self.call(self._all_adapters[i-1], adapter_call_arguments)
                if rv == None: return i
                else: return rv
            except Exception as exc:
                if 'adapter_exception_handler' in self._variables:
                    return self.call_exception_handler('adapter_exception_handler', self._all_names[i-1], exc)
                else:
                    raise
            finally:
                fmbt._g_testStep -= 1
                fmbt._g_lastExecutedActionName = fmbt._g_actionName
        else:
            self._log("AAL model: adapter_execute for an output action in AAL." +
                      "This should take place in observe().\n")
            return 0

    def tag_execute(self, i):
        if not 0 < i <= len(self._all_tagnames):
            raise IndexError('Cannot execute tag %s adapter code' % (i,))
        fmbt._g_actionName = "tag: " + self._all_tagnames[i-1]
        try:
            rv = self.call(self._all_tagadapters[i-1])
        except Exception as exc:
            if 'adapter_exception_handler' in self._variables:
                return self.call_tagexception_handler('adapter_exception_handler', self._all_tagnames[i-1], exc)
            else:
                raise
        return rv

    def model_execute(self, i):
        if not 0 < i <= len(self._all_names):
            # If adapter execute returns 0, that is reports unidentified action,
            # test engine checks if executing an unidentified action is ok by
            # calling model_execute(0). In AAL/Python it is never ok.
            return 0
        fmbt._g_actionName = self._all_names[i-1]
        if i in self._enabled_actions_stack[-1] or self.call(self._all_guards[i-1]):
            self.call(self._all_bodies[i-1])
            if self._has_serial:
                for postfunc in getattr(self, self._all_bodies[i-1].__name__ + "_postcall", []):
                    getattr(self, postfunc)(fmbt._g_actionName)
            if len(self._stack) == 0:
                fmbt._g_testStep += 1
            if len(self._stack_executed_actions) > 0:
                self._stack_executed_actions[-1].append(fmbt._g_actionName)
            self._enabled_actions_stack[-1] = set()
            return i
        else:
            self._enabled_actions_stack[-1] = set()
            return 0

    def getActions(self):
        enabled_actions = []
        for index, guard in enumerate(self._all_guards):
            fmbt._g_actionName = self._all_names[index]
            if self.call(guard): enabled_actions.append(index + 1)
        self._enabled_actions_stack[-1] = set(enabled_actions)
        return enabled_actions

    def getIActions(self):
        enabled_iactions = []
        try:
            for index, guard in enumerate(self._all_guards):
                fmbt._g_actionName = self._all_names[index]
                if self._all_types[index] == "input" and self.call(guard):
                    enabled_iactions.append(index + 1)
        except Exception as e:
            raise Exception('Error at guard() of "%s": %s: %s' % (
                self._all_names[index], type(e).__name__, e))
        self._enabled_actions_stack[-1].update(enabled_iactions)
        return enabled_iactions

    def getprops(self):
        enabled_tags = []
        for index, guard in enumerate(self._all_tagguards):
            fmbt._g_actionName = "tag: " + self._all_tagnames[index]
            if self.call(guard): enabled_tags.append(index + 1)
        return enabled_tags

    def getActionNames(self):
        return self._all_names

    def getSPNames(self):
        return self._all_tagnames

    def push(self, obj=None):
        """
        Push current state (or optional parameter obj) to the stack.

        See also: pop(), state_obj().
        """
        if obj != None:
            self._stack.append(obj[0])
            self._stack_executed_actions.append(obj[1])
            self._enabled_actions_stack.append(obj[2])
            return
        # initial state must reset all variables.
        # automatic push saves only their states
        stack_element = {}
        for varname in self._push_variables:
            val = self._variables[varname]
            if type(val) in _g_immutable_types:
                stack_element[varname] = val
            else:
                stack_element[varname] = copy.deepcopy(val)
        if self._has_serial:
            stack_element["!serial_abn"] = copy.deepcopy(self._get_all("guard_next_block", "serial"))
        self._stack.append(stack_element)
        self._stack_executed_actions.append([])
        self._enabled_actions_stack.append(set(self._enabled_actions_stack[-1]))

    def pop(self):
        """
        Pop the topmost state in the stack and start using it as the
        current state.

        See also: push()
        """
        stack_element = self._stack.pop()
        self._stack_executed_actions.pop()
        for varname in stack_element:
            if varname.startswith("!"): continue
            self._variables[varname] = stack_element[varname]
        if self._has_serial:
            self._set_all_class("guard_next_block", "serial", stack_element["!serial_abn"])
        self._enabled_actions_stack.pop()

    def stack_top(self):
        return self._stack[-1], self._stack_executed_actions[-1], self._enabled_actions_stack[-1]

    def stack_discard(self):
        self._stack.pop()
        self._stack_executed_actions.pop()
        self._enabled_actions_stack.pop()

    def state_obj(self):
        """
        Return current state as a Python object
        """
        self.push()
        obj = self.stack_top()
        self.stack_discard()
        return obj

    def state_obj_copy(self, obj=None):
        """
        Return copy of a state_obj.
        Faster than copy.deepcopy(self.state_obj())
        """
        if obj == None:
            obj = self.state_obj()
        stack_top, stack_executed_top, stack_enabled_top = obj
        copy_stack_top = {}
        for varname in self._push_variables:
            val = stack_top[varname]
            if type(val) in _g_immutable_types:
                copy_stack_top[varname] = val
            else:
                copy_stack_top[varname] = copy.deepcopy(val)
        if self._has_serial:
            copy_stack_top["!serial_abn"] = copy.deepcopy(stack_top["!serial_abn"])
        copy_stack_executed_top = list(stack_executed_top)
        copy_stack_enabled_top = set(stack_enabled_top)
        return copy_stack_top, copy_stack_executed_top, copy_stack_enabled_top

    def set_state_obj(self, obj):
        """
        Set obj as current state. See also state_obj().
        """
        self.push(obj)
        self.pop()

    def state(self, discard_variables=None, include_variables=None):
        """
        Return the current state of the model as a string.
        By comparing strings one can check if the state is already seen.
        """
        rv_list = []
        for varname in self._push_variables:
            if ((include_variables and not varname in include_variables) or
                (discard_variables and varname in discard_variables)):
                continue
            rv_list.append(varname + " = " + repr(self._variables[varname]))
        if self._has_serial:
            rv_list.append("!serial = " + str(self._get_all("guard_next_block", "serial")))
        return '\n'.join(rv_list)

    def observe(self, block):
        poll_more = True
        start_time = 0

        # Executing adapter blocks of output actions is allowed to
        # change the state of the model. Allow execution of outputs
        # whose guards are true both before executing adapter blocks*
        # or after it. For that purpose, add currently enabled output
        # actions to enabled_actions_stack.
        enabled_oactions = []
        for index, guard in enumerate(self._all_guards):
            fmbt._g_actionName = self._all_names[index]
            if (self._all_types[index] == "output" and
                not (index + 1) in self._enabled_actions_stack[-1] and
                self.call(guard)):
                enabled_oactions.append(index + 1)
        self._enabled_actions_stack[-1].update(enabled_oactions)

        while poll_more:
            for index, adapter in enumerate(self._all_adapters):
                if self._all_types[index] != "output": continue
                fmbt._g_actionName = self._all_names[index]
                try:
                    fmbt._g_testStep += 1
                    output_action = self.call(adapter)
                except Exception as exc:
                    if 'adapter_exception_handler' in self._variables:
                        output_action = self.call_exception_handler(
                            'adapter_exception_handler',
                            self._all_names[index], exc,
                            pass_through_rv = [False])
                    else:
                        raise
                finally:
                    fmbt._g_testStep -= 1
                observed_action = None
                if type(output_action) == str:
                    observed_action = self._all_names.index(output_action) + 1
                elif type(output_action) == type(True) and output_action == True:
                    observed_action = index + 1
                elif type(output_action) == int and output_action > 0:
                    observed_action = output_action

                if observed_action:
                    self._log('observe: action "%s" adapter() returned %s. Reporting "%s"' % (
                            self._all_names[index], output_action,
                            self._all_names[observed_action-1]))
                    fmbt._g_lastExecutedActionName = self._all_names[observed_action-1]
                    return [observed_action]
            if block:
                if not start_time: start_time = time.time()
                elif time.time() - start_time > self.timeout:
                    return [SILENCE]
            else:
                poll_more = False
        return [SILENCE]
