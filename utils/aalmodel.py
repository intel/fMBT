import copy
import types
import time
import traceback
import fmbt

SILENCE = -3

def setCodeFileLine(c, filename, lineno, funcname=None):
    if funcname == None:
        funcname = c.co_name
    return types.CodeType(
        c.co_argcount, c.co_nlocals, c.co_stacksize, c.co_flags,
        c.co_code, c.co_consts, c.co_names, c.co_varnames,
        filename, funcname, lineno, c.co_lnotab, c.co_freevars)

class AALModel:
    def __init__(self, model_globals):
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
            try: plist.append(getattr(self, itemtype + str(i) + property_name))
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

    def call(self, func, call_arguments = ()):
        guard_list = None
        try:
            func_name = func.__name__
            if func_name.endswith("guard"):
                guard_list = self._variables['guard_list']
                guard_list.append(
                    getattr(self, func_name.replace("guard", "name"), ""))
            fmbt._g_simulated_actions = self._stack_executed_actions
            if hasattr(func,"requires"):
                for prerequire in func.requires:
                    if not self.call(getattr(self,prerequire)):
                        return False
            args = []
            for arg in call_arguments:
                if arg == '':
                    args.append('')
                else:
                    args.append(eval(arg, self._variables))
            self._variables['args'] = args
            return eval(func.func_code, self._variables)
        except Exception, e:
            self._log("Exception %s in %s: %s" % (e.__class__, func.func_name, e))
            self._log(traceback.format_exc())
            raise
        finally:
            if guard_list != None:
                guard_list.pop()

    def call_exception_handler(self, handler_name, action_name, exc):
        rv = self._variables[handler_name](action_name, exc)
        if type(rv) == int:
            return rv
        elif rv == None or rv == True:
            return self._variables['action'](action_name)
        else:
            raise Exception('''Exception handler "%s('%s', %s)" returned unexpected value: %s''' %
                            (handler_name, action_name, exc, rv))

    def reset(self):
        # initialize model
        fmbt._g_actionName = "AAL: initial_state"
        rv = self.call(self.initial_state)
        self._push_variables = [
            v for v in self.__class__.push_variables_set
            if (v in self._variables and
                type(eval(v, self._variables)) not in [types.ModuleType, types.ClassType])
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
            self.adapter_exit.im_func(verdict, reason)

    def adapter_execute(self, i, adapter_call_arguments = ()):
        if not 0 < i <= len(self._all_names):
            raise IndexError('Cannot execute action %s adapter code' % (i,))
        if self._all_types[i-1] == "input":
            try:
                fmbt._g_actionName = self._all_names[i-1]
                fmbt._g_testStep += 1
                rv = self.call(self._all_adapters[i-1], adapter_call_arguments)
                fmbt._g_testStep -= 1
                if rv == None: return i
                else: return rv
            except Exception, exc:
                if 'adapter_exception_handler' in self._variables:
                    return self.call_exception_handler('adapter_exception_handler', self._all_names[i-1], exc)
                else:
                    raise
        else:
            self._log("AAL model: adapter_execute for an output action in AAL." +
                      "This should take place in observe().\n")
            return 0

    def tag_execute(self, i):
        if not 0 < i <= len(self._all_tagnames):
            raise IndexError('Cannot execute tag %s adapter code' % (i,))
        fmbt._g_actionName = "tag: " + self._all_tagnames[i-1]
        rv = self.call(self._all_tagadapters[i-1])
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
        except Exception, e:
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

    def push(self):
        # initial state must reset all variables.
        # automatic push saves only their states
        stack_element = {}
        for varname in self._push_variables:
            stack_element[varname] = copy.deepcopy(self._variables[varname])
        if self._has_serial:
            stack_element["!serial_abn"] = copy.deepcopy(self._get_all("guard_next_block", "serial"))
        self._stack.append(stack_element)
        self._stack_executed_actions.append([])
        self._enabled_actions_stack.append(set(self._enabled_actions_stack[-1]))

    def pop(self):
        stack_element = self._stack.pop()
        self._stack_executed_actions.pop()
        for varname in stack_element:
            if varname.startswith("!"): continue
            self._variables[varname] = stack_element[varname]
        if self._has_serial:
            self._set_all_class("guard_next_block", "serial", stack_element["!serial_abn"])
        self._enabled_actions_stack.pop()

    def state(self, discard_variables = set([]), include_variables=None):
        """
        Return the current state of the model as a string.
        By comparing strings one can check if the state is already seen.
        """
        rv_list = []
        for varname in self._push_variables:
            if ((include_variables and not varname in include_variables) or
                (varname in discard_variables)):
                continue
            rv_list.append("%s = %s" % (varname, repr(self._variables[varname])))
        if self._has_serial:
            rv_list.append("!serial = %s" % (self._get_all("guard_next_block", "serial"),))
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
                output_action = self.call(adapter)
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
                    return [observed_action]
            if block:
                if not start_time: start_time = time.time()
                elif time.time() - start_time > self.timeout:
                    return [SILENCE]
            else:
                poll_more = False
        return [SILENCE]
