class AALModel:
    def __init__(self):
        self._all_guards = self._get_all("guard")
        self._all_bodies = self._get_all("body")
        self._all_adapters = self._get_all("adapter")
        self._all_names = self._get_all("name")
        self._all_types = self._get_all("type")

    def _get_all(self, property_name):
        plist = []
        i = 0
        while 1:
            try: plist.append(getattr(self, "action" + str(i) + property_name))
            except: return plist
            i += 1

    def adapter_execute(self, i):
        return self._all_adapters[i]()

    def model_execute(self, i):
        return self._all_bodies[i]()

    def getActions(self):
        enabled_actions = []
        for index, guard in enumerate(self._all_guards):
            if guard(): enabled_actions.append(index)
        return enabled_actions
    
    def getIActions(self):
        enabled_iactions = []
        for index, guard in enumerate(self._all_guards):
            if self._all_types[index] == "input" and guard():
                enabled_iactions.append(index)
        return enabled_iactions

    def getActionNames(self):
        return self._all_names
