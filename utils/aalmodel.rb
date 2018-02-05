class AALModel
    attr_accessor :log 
    attr_accessor :timeout
    @@SILENCE = -3

    def initialize()
        @immutable_types = Set.new(["String", "Fixnum", "Long", "Float", "TrueClass", "NilClass", "Array"])

        @variables = {}
        @variables['guard_list'] = []

        @aal_block_name = {}
        @all_guards = get_all("guard", "action")
        @all_bodies = get_all("body", "action")
        @all_adapters = get_all("adapter", "action")
        @all_names = get_all("name", "action")
        @all_types = get_all("type","action")

        @all_tagnames = get_all("name", "tag")
        @all_tagguards = get_all("guard", "tag")
        @all_tagadapters = get_all("adapter", "tag")
        
        if get_all("guard_next_block", "serial").length > 0
            @has_serial = true
        else
            @has_serial = false
        end

        @stack = []
        @enabled_actions_stack = [Set.new()]
        @stack_executed_actions = []
        @push_variables = []
    end
    def call(func_name, call_arguments=nil)
        guard_list = nil
        begin
            Fmbt.simulated_actions = @stack_executed_actions
            if func_name[-1,1] == "d" # faster than func_name.endswith("guard")
                guard_list = @variables['guard_list']
                guard_list.push(@aal_block_name[func_name])
                #todo  dont konw what is it
                # for prerequisite in func.requires
                    # if not self.call(getattr(self, prerequisite))
                    #     return False
                    # end
                # end
            end
            if call_arguments
                args = []
                for arg in call_arguments
                    if arg == ''
                        args.push('')
                    else
                        args.push(eval(arg, self._variables))
                    end
                end
                @variables['args'] = args
            else
                @variables['args'] = []
            end
            rv = self.send(func_name)
            if guard_list
                guard_list.pop()
            end
            return rv
        rescue Exception, e
            @log.log("Exception #{e.class} in #{func.func_name} #{e.message}")
            @log.log(traceback.format_exc())
            if guard_list
                guard_list.pop()
            raise
            end
        end
    end

    def get_all(property_name, itemtype)
        plist = []
        i = 1
        while true
            obj = self.instance_variable_get("@#{itemtype}#{i}#{property_name}")
            if obj != nil
                plist.push(obj)
            else 
                #methos in ruby 1.8.6 returns string
                obj = self.methods.include?("#{itemtype}#{i}#{property_name}")
                #methods in ruby 2.3 returns symbol
                obj_symbol_check = self.methods.include?("#{itemtype}#{i}#{property_name}".to_sym)
                if obj or obj_symbol_check
                    if ["guard", "body", "adapter"].include?(property_name) and ["action", "tag"].include?(itemtype)
                        @aal_block_name["#{itemtype}#{i}#{property_name}"] = self.instance_variable_get("@#{itemtype}#{i}name")
                    elsif itemtype == "serial"
                        @aal_block_name["serial#{i}#{property_name}"] = self.instance_variable_get("@serial#{i}name")
                    end
                    plist.push("#{itemtype}#{i}#{property_name}")
                else
                    return plist
                end
            end
            i += 1
        end
    end

    def getActions()
        enabled_actions = []
        @all_guards.each_with_index do |guard,index|
            Fmbt.actionName = @all_names[index]
            if call(guard)
                enabled_actions.push(index + 1)
            end
        end
        @enabled_actions_stack[-1] = Set.new(enabled_actions)
        return enabled_actions
    end
    
    def getActionNames()
        return @all_names
    end

    def getSPNames()
        return @all_tagnames
    end

    def push(obj=nil)
        """
        Push current state (or optional parameter obj) to the stack.

        See also pop(), state_obj().
        """
        if obj != nil
            @stack.push(obj[0])
            @stack_executed_actions.push(obj[1])
            @enabled_actions_stack.push(obj[2])
            return
        end
        # initial state must reset all variables.
        # automatic push saves only their states
        stack_element = {}
        for varname in @push_variables
            val = @variables[varname]
            if @immutable_types.include?(val.class)
                stack_element[varname] = val
            else
                #todo  deep copy
                stack_element[varname] = val
            end 
        end
        if @has_serial
            #todo  deep copy
            stack_element["!serial_abn"] = get_all("guard_next_block", "serial")
        end
        @stack.push(stack_element)
        @stack_executed_actions.push([])
        @enabled_actions_stack.push(Set.new(@enabled_actions_stack[-1]))
    end

    def pop()
        """
        Pop the topmost state in the stack and start using it as the
        current state.

        See also push()
        """
        stack_element = @stack.pop()
        @stack_executed_actions.pop()
        for varname in stack_element
            if varname[0..1] == "!"
                 next 
            end
            @variables[varname] = stack_element[varname]
        end
        if @has_serial
            set_all_class("guard_next_block", "serial", stack_element["!serial_abn"])
        end
        @enabled_actions_stack.pop() 
    end
    
    def stack_top()
        return @stack[-1], @stack_executed_actions[-1], @enabled_actions_stack[-1]
    end
    
    def stack_discard()
        @stack.pop()
        @stack_executed_actions.pop()
        @enabled_actions_stack.pop()
    end

    def state_obj()
        """
        Return current state as a Python object
        """
        push()
        obj = stack_top()
        stack_discard()
        return obj
    end

    def set_all_class(property_name, itemtype, value_array)
        i = 1
        cls = self.class
        while true
            itemname = itemtype + i.to_s + property_name
            if self.instance_variable.include?(itemname)
                self.instance_variable_set(itemname, value_array[i-1])
            else
                return
            end
            i += 1
        end 
    end

    def set_state_obj(obj):
        """
        Set obj as current state. See also state_obj().
        """
        push(obj)
        pop() 
    end

    def state_obj_copy(obj=nil):
        """
        Return copy of a state_obj.
        Faster than copy.deepcopy(self.state_obj())
        """
        if obj == nil:
            obj = state_obj()
        end
        stack_top, stack_executed_top, stack_enabled_top = obj
        copy_stack_top = {}
        for varname in @push_variables
            val = stack_top[varname]
            if @immutable_types.include?(val.class)
                copy_stack_top[varname] = val
            else
                #todo : deepcopy
                copy_stack_top[varname] = copy.deepcopy(val)
            end
        end
        if @has_serial:
            #todo : ddeepcopy
            copy_stack_top["!serial_abn"] = stack_top["!serial_abn"]
        end
        copy_stack_executed_top = list(stack_executed_top)
        copy_stack_enabled_top = Set.new(stack_enabled_top)
        return copy_stack_top, copy_stack_executed_top, copy_stack_enabled_top
    end 
    
    def reset()
        # initialize model
        Fmbt.actionName = "AAL initial_state"
        rv = call('initial_state')
        for v in @push_variables_set
            @push_variables.push(v)
        end
        return rv
    end

    def init()
        # initialize adapter
        Fmbt.actionName = "AAL adapter_init"
        rv = call('adapter_init')
        return rv
    end
    
    #getting enabled tags
    def getprops()
        enabled_tags = []
        @all_tagguards = get_all("guard", "tag")
        @all_tagguards.each_with_index do |guard,index|
            Fmbt.actionName = "tag " + @all_tagnames[index]
            if call(guard)
                enabled_tags.push(index + 1)
            end
        end
        return enabled_tags
    end

    def tag_execute(i)
        if not (i > 0 and i <= @all_tagnames.length)
            raise IndexError.new("Cannot execute tag #{i} adapter code")
        end
        Fmbt.actionName = "tag " + @all_tagnames[i-1]
        begin
            rv = call(@all_tagadapters[i-1])
        rescue Exception => e
            if  @variables.include?('adapter_exception_handler')
                return call_tagexception_handler('adapter_exception_handler', @all_tagnames[i-1], exc)
            else
                raise
            end
        end
        return rv
    end

    def state(discard_variables=nil, include_variables=nil)
        """
        Return the current state of the model as a string.
        By comparing strings one can check if the state is already seen.
        """
        rv_list = []
        for varname in @push_variables
            if (include_variables and not include_variables.include?(varname)) or (discard_variables and discard_variables.include?(varname))
                next
            end
            rv_list.push("#{varname} = '#{eval("$#{varname}")}'")
        end
        if @has_serial
            rv_list.push("!serial = #{get_all("guard_next_block", "serial")}")
        end
        return rv_list.join('\n')
    end
       
    def observe(block)
        poll_more = true
        start_time = 0
        
        # Executing adapter blocks of output actions is allowed to
        # change the state of the model. Allow execution of outputs
        # whose guards are true both before executing adapter blocks*
        # or after it. For that purpose, add currently enabled output
        # actions to enabled_actions_stack.
        enabled_oactions = []
        @all_guards.each_with_index do |guard,index|
            Fmbt.actionName = @all_names[index]
            if @all_types[index] == "output" and not @enabled_actions_stack[-1].include?(index + 1)  and call(guard)
                enabled_oactions.append(index + 1)
            end
        end
        @enabled_actions_stack[-1].merge(enabled_oactions)

        while poll_more
            @all_adapters.each_with_index do |adapter,index|
                if @all_types[index] != "output"
                    next
                end
                Fmbt.actionName = @all_names[index]
                begin
                    fmbt._g_testStep += 1
                    output_action = self.call(adapter)
                rescue Exception => e
                    if @variables.include?('adapter_exception_handler')
                        output_action = call_exception_handler(
                            'adapter_exception_handler',
                            @all_names[index], exc,
                            pass_through_rv = [False])
                    else
                        raise
                    end
                ensure
                    Fmbt.testStep -= 1
                end
                observed_action = None
                if type(output_action) == str
                    observed_action = @all_names.index(output_action) + 1
                elsif type(output_action) == type(True) and output_action
                    observed_action = index + 1
                elsif type(output_action) == int and output_action > 0
                    observed_action = output_action
                end
                if observed_action
                    log.log("observe action \"#{@all_names[index]}\" adapter() returned #{output_action}. Reporting \"#{@all_names[observed_action-1]}\"")
                    Fmbt.lastExecutedActionName = @all_names[observed_action-1]
                    return [observed_action]
                end
            end
            if block
                if not start_time
                     start_time = time.time()
                elsif time.time() - start_time > timeout
                    return [@@SILENCE]
                end
            else
                poll_more = false
            end
        end
        return [@@SILENCE]
    end
     
    
end