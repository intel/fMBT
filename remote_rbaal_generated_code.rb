require 'tempfile'

require 'fileutils'



$DIRNAME = Tempfile.new("test").path

dir_array = $DIRNAME.split("/")

$DIRNAME = dir_array[0..dir_array.length-2].join("/") + "/fmbt.filesystemtest"

$SUBDIRNAME = $DIRNAME + "/subdir"
require 'g:/programming/MBT/fMBT/utils/aalmodel.rb'
require 'set'

class Gen_filesystemtest < AALModel
    

    def initialize()
        @adapter_init_list = []
        @initial_state_list = []
        @adapter_exit_list = []
        @push_variables_set = Set.new()
        
        @action1name = "i:mkdir: ok"
        @action1type = "input"
        @action2name = "i:rmdir ok"
        @action2type = "input"
        @action3name = "i:mksubdir ok"
        @action3type = "input"
        @action4name = "i:rmsubdir ok"
        @action4type = "input"
        @action5name = "i:mkdir already exists"
        @action5type = "input"
        @action6name = "i:mksubdir already exists"
        @action6type = "input"
        @action7name = "i:rmdir no such file"
        @action7type = "input"
        @action8name = "i:rmdir not empty"
        @action8type = "input"
        @action9name = "i:rmsubdir no such file"
        @action9type = "input"
        @tag1name = "dir exists"
        @tag2name = "no dir"
        @tag3name = "subdir exists"
        @tag4name = "no subdir"

        @initial_state_list.push('initial_state1')
        @adapter_init_list.push('adapter_init1')
        super()
    end
    
    def initial_state1()
        dir_exists = false
        subdir_exists = false
        user_definedd_variable = local_variables
        user_definedd_variable.pop() # remove "_" from ["dir_exists", "subdir_exists", "_"]
        user_definedd_variable.each do |item|
            @push_variables_set.add(item)
            @variables[item] = "#{eval(item)}"
        end
        
    end

    def adapter_init1()
        begin
            FileUtils.rm_rf("#{$DIRNAME}/.")
        rescue Exception => e
        end
        return 1
    end

    def adapter_exit1(verdict,reason)
        global dir_exists, subdir_exists
        if verdict == "" and dir_exists

            log("cleaning up " + $DIRNAME)

            begin

                FileUtils.rm_rf("#{$DIRNAME}/.")

            rescue Exception => e
            end

        end
        @adapter_exit_list.push(adapter_exit1)
    end
    
    def action1guard()
        global dir_exists, subdir_exists
        action_name = "i:mkdir ok"
        input_name ="mkdir ok"
        action_index = 0
        return ! dir_exists
    end
    def action1body()
        global dir_exists, subdir_exists
        action_name = "i:mkdir ok"
        input_name ="mkdir ok"
        action_index = 0
        dir_exists = true
    end
    def action1adapter()
        global dir_exists, subdir_exists
        action_name = "i:mkdir ok"
        input_name ="mkdir ok"
        action_index = 0
        Dir.mkdir($DIRNAME)
        return 1
    end


    
    def action2guard()
        global dir_exists, subdir_exists
        action_name = "i:rmdir ok"
        input_name ="rmdir ok"
        action_index = 0
        return dir_exists && ! subdir_exists
    end
    def action2body()
        global dir_exists, subdir_exists
        action_name = "i:rmdir ok"
        input_name ="rmdir ok"
        action_index = 0
        dir_exists = false
    end
    def action2adapter()
        global dir_exists, subdir_exists
        action_name = "i:rmdir ok"
        input_name ="rmdir ok"
        action_index = 0
        Dir.rmdir($DIRNAME)
        return 2
    end

    def action3guard()
        global dir_exists, subdir_exists
        action_name = "i:mksubdir ok"
        input_name ="mksubdir ok"
        action_index = 0
        return dir_exists && ! subdir_exists
    end
    def action3body()
        global dir_exists, subdir_exists
        action_name = "i:mksubdir ok"
        input_name ="mksubdir ok"
        action_index = 0
        subdir_exists = true
    end
    def action3adapter()
        global dir_exists, subdir_exists
        action_name = "i:mksubdir ok"
        input_name ="mksubdir ok"
        action_index = 0
        Dir.mkdir($SUBDIRNAME)
        return 3
    end


    def action4guard()
        global dir_exists, subdir_exists
        action_name = "i:rmsubdir ok"
        input_name ="rmsubdir ok"
        action_index = 0
        return subdir_exists
    end
    def action4body()
        global dir_exists, subdir_exists
        action_name = "i:rmsubdir ok"
        input_name ="rmsubdir ok"
        action_index = 0
        subdir_exists = false
    end
    def action4adapter()
        global dir_exists, subdir_exists
        action_name = "i:rmsubdir ok"
        input_name ="rmsubdir ok"
        action_index = 0
        Dir.rmdir($SUBDIRNAME)
        return 4
    end
    
    def action5guard()
        global dir_exists, subdir_exists
        action_name = "i:mkdir already exists"
        input_name ="mkdir already exists"
        action_index = 0
        return dir_exists
    end
    def action5body()
        global dir_exists, subdir_exists
        action_name = "i:mkdir already exists"
        input_name ="mkdir already exists"
        action_index = 0
        
    end
    def action5adapter()
        global dir_exists, subdir_exists
        action_name = "i:mkdir already exists"
        input_name ="mkdir already exists"
        action_index = 0
        begin 

            os.mkdir($DIRNAME)

        rescue Errno::EEXIST => e

            if e.to_s.include?("File exists")

                return

            end

        end

        raise(StandardError,"Exception expected")
        return 5
    end


    
    def action6guard()
        global dir_exists, subdir_exists
        action_name = "i:mksubdir already exists"
        input_name ="mksubdir already exists"
        action_index = 0
        return subdir_exists
    end
    def action6body()
        global dir_exists, subdir_exists
        action_name = "i:mksubdir already exists"
        input_name ="mksubdir already exists"
        action_index = 0
        
    end
    def action6adapter()
        global dir_exists, subdir_exists
        action_name = "i:mksubdir already exists"
        input_name ="mksubdir already exists"
        action_index = 0
        begin

            Dir.mkdir($SUBDIRNAME)

        rescue Errno::EEXIST => e

            if e.to_s.include?("File exists")

                return

            end

        end

        raise(StandardError,"Exception expected")
        return 6
    end
    
    def action7guard()
        global dir_exists, subdir_exists
        action_name = "i:rmdir no such file"
        input_name ="rmdir no such file"
        action_index = 0
        return ! dir_exists
    end
    def action7body()
        global dir_exists, subdir_exists
        action_name = "i:rmdir no such file"
        input_name ="rmdir no such file"
        action_index = 0
        
    end
    def action7adapter()
        global dir_exists, subdir_exists
        action_name = "i:rmdir no such file"
        input_name ="rmdir no such file"
        action_index = 0
        begin

            Dir.rmdir($DIRNAME)

        rescue Errno::ENOENT => e

            if e.to_s.include?("No such file or directory")

                return

            end

        end

        raise(StandardError,"Exception expected")
        return 7
    end


    
    def action8guard()
        global dir_exists, subdir_exists
        action_name = "i:rmdir not empty"
        input_name ="rmdir not empty"
        action_index = 0
        return subdir_exists
    end
    def action8body()
        global dir_exists, subdir_exists
        action_name = "i:rmdir not empty"
        input_name ="rmdir not empty"
        action_index = 0
        
    end
    def action8adapter()
        global dir_exists, subdir_exists
        action_name = "i:rmdir not empty"
        input_name ="rmdir not empty"
        action_index = 0
        begin

            Dir.rmdir($DIRNAME)

        rescue Errno::ENOTEMPTY => e

            if e.to_s.include?("Directory not empty")

                return

            end

        end

        raise(StandardError,"Exception expected")
        return 8
    end
    
    def action9guard()
        global dir_exists, subdir_exists
        action_name = "i:rmsubdir no such file"
        input_name ="rmsubdir no such file"
        action_index = 0
        return ! subdir_exists
    end
    def action9body()
        global dir_exists, subdir_exists
        action_name = "i:rmsubdir no such file"
        input_name ="rmsubdir no such file"
        action_index = 0
        
    end
    def action9adapter()
        global dir_exists, subdir_exists
        action_name = "i:rmsubdir no such file"
        input_name ="rmsubdir no such file"
        action_index = 0
        begin

            Dir.rmdir($SUBDIRNAME)

        rescue Errno::ENOENT => e

            if e.to_s.include?("No such file or directory")

                return

            end

        end

        raise(StandardError,"Exception expected")
        return 9
    end


    
    def tag1guard()
        tag_name = "dir exists"
        return $dir_exists
    end
    def tag1adapter()
        tag_name = "dir exists"
        if not File.directory?($DIRNAME)
            raise("#{$DIRNAME} not accessible")
        end
    end

    def tag2guard()
        tag_name = "no dir"
        return ! $dir_exists
    end
    def tag2adapter()
        tag_name = "no dir"
        if File.directory?($DIRNAME)
            raise("#{$DIRNAME}  accessible")
        end
    end
 
    def tag3guard()
        tag_name = "subdir exists"
        return $subdir_exists
    end
    def tag3adapter()
        tag_name = "subdir exists"
        if not File.directory?($SUBDIRNAME)
            raise("#{$SUBDIRNAME} not accessible")
        end
    end

    def tag4guard()
        tag_name = "no subdir"
        return ! $subdir_exists
    end
    def tag4adapter()
        tag_name = "no subdir"
        if File.directory?($SUBDIRNAME)
            raise("#{$SUBDIRNAME}  accessible")
        end
    end

    def adapter_init()
        for x in @adapter_init_list
            ret = self.send(x)
            if not ret and ret != nil
                return ret
            end
        end
        return true
    end
    def initial_state()
        for x in @initial_state_list
            ret = self.send(x)
            if not ret and ret != nil
                return ret
            end
        end
        return true
    end
    def adapter_exit(verdict,reason)
        for x in @adapter_exit_list
            ret = x(verdict,reason)
            if not ret and ret != None
                return ret
            end
        end
        return True
    end
end

class Model < Gen_filesystemtest
    def initialize()
        super()
    end
end