import copy

class AALModel:
    def __init__(self):
        self._all_guards = self._get_all("guard", "action")
        self._all_bodies = self._get_all("body", "action")
        self._all_adapters = self._get_all("adapter", "action")
        self._all_names = self._get_all("name", "action")
        self._all_types = self._get_all("type", "action")
        self._all_tagnames = self._get_all("name", "tag")
        self._all_tagguards = self._get_all("guard", "tag")
        self._variables = globals()
        self._stack = []

    def _get_all(self, property_name, itemtype):
        plist = []
        i = 1
        while 1:
            try: plist.append(getattr(self, itemtype + str(i) + property_name))
            except: return plist
            i += 1

    def call(self, func):
        return eval(func.func_code, self._variables)

    def reset(self):
        self.call(self.initial_state)

    def adapter_execute(self, i):
        return self.call(self._all_adapters[i-1])

    def model_execute(self, i):
        return self.call(self._all_bodies[i-1])

    def getActions(self):
        enabled_actions = []
        for index, guard in enumerate(self._all_guards):
            if self.call(guard): enabled_actions.append(index + 1)
        return enabled_actions
    
    def getIActions(self):
        enabled_iactions = []
        for index, guard in enumerate(self._all_guards):
            if self._all_types[index] == "input" and self.call(guard):
                enabled_iactions.append(index + 1)
        return enabled_iactions

    def getprops(self):
        enabled_tags = []
        for index, guard in enumerate(self._all_tagguards):
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
        for varname in self.initial_state.func_code.co_names:
            stack_element[varname] = copy.deepcopy(self._variables[varname])
        self._stack.append(stack_element)

    def pop(self):
        stack_element = self._stack.pop()
        for varname in stack_element:
            self._variables[varname] = stack_element[varname]
