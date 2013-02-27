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
        self._variables = model_globals
        self._variables['action'] = lambda name: self._all_names.index(name) + 1
        self._variables['name'] = lambda name: self._all_names.index(name)
        self._variables['variable'] = lambda varname: self._variables[varname]
        self._variables['assign'] = lambda varname, v: self._variables.__setitem__(varname, v)
        self._stack = []
        fmbt._g_testStep = 1

    def _get_all(self, property_name, itemtype):
        plist = []
        i = 1
        while 1:
            try: plist.append(getattr(self, itemtype + str(i) + property_name))
            except: return plist
            i += 1

    def call(self, func, call_arguments = ()):
        try:
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
        fmbt._g_actionName = "undefined"
        rv = self.call(self.initial_state)
        self._push_variables = [
            v for v in self.initial_state.func_code.co_names
            if (v in self._variables and
                type(eval(v, self._variables)) not in [types.ModuleType, types.ClassType])
            ]
        return rv

    def adapter_init():
        return True

    def init(self):
        # initialize adapter
        fmbt._g_actionName = "undefined"
        rv = self.call(self.adapter_init)
        return rv

    def adapter_execute(self, i, adapter_call_arguments = ()):
        if self._all_types[i-1] == "input":
            try:
                fmbt._g_actionName = self._all_names[i-1]
                rv = self.call(self._all_adapters[i-1], adapter_call_arguments)
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

    def model_execute(self, i):
        fmbt._g_actionName = self._all_names[i-1]
        if self.call(self._all_guards[i-1]):
            self.call(self._all_bodies[i-1])
            if len(self._stack) == 0:
                fmbt._g_testStep += 1
            return i
        else:
            return 0

    def getActions(self):
        enabled_actions = []
        try:
            for index, guard in enumerate(self._all_guards):
                fmbt._g_actionName = self._all_names[index]
                if self.call(guard): enabled_actions.append(index + 1)
        except Exception, e:
            raise Exception('Error at guard() of "%s": %s: %s\n%s' % (
                self._all_names[index], type(e).__name__, e, traceback.format_exc()))
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
        return enabled_iactions

    def getprops(self):
        enabled_tags = []
        for index, guard in enumerate(self._all_tagguards):
            fmbt._g_actionName = "undefined"
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
        self._stack.append(stack_element)

    def pop(self):
        stack_element = self._stack.pop()
        for varname in stack_element:
            self._variables[varname] = stack_element[varname]

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
        return '\n'.join(rv_list)

    def observe(self, block):
        poll_more = True
        start_time = 0
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
