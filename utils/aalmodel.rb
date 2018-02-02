class AALModel
    attr_accessor :_log 
    attr_accessor :timeout

    def initialize()
        @variables = {}
        @all_names = get_all("name", "action")
        @all_tagnames = get_all("name", "tag")
    end

    def get_all(property_name, itemtype)
        plist = []
        i = 1
        while true
            obj = self.instance_variable_get(:"@#{itemtype}#{i}#{property_name}")
            if obj != nil
                plist.push(obj)
            else 
                return plist
            end
            i += 1
        end
    end

    def getActionNames()
        return @all_names
    end

    def getSPNames()
        return @all_tagnames
    end
end