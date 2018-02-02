import os
import shutil
import tempfile
MOUNTPOINT = tempfile.tempdir
DIRNAME = os.path.join( MOUNTPOINT , "fmbt.filesystemtest" )
SUBDIRNAME = os.path.join( DIRNAME , "subdir" )
import aalmodel
class _gen_filesystemtest(aalmodel.AALModel):
    def __init__(self):
        aalmodel.AALModel.__init__(self, globals())
    adapter_init_list = []
    initial_state_list = []
    adapter_exit_list = []
    push_variables_set = set()

    def initial_state1():
        global dir_exists, subdir_exists
        dir_exists = False
        subdir_exists = False
        pass
    initial_state1.func_code = aalmodel.setCodeFileLine(initial_state1.func_code, '''examples\filesystemtest\filesystemtest.aal''', 11)
    initial_state_list.append(initial_state1)
    push_variables_set.update(initial_state1.func_code.co_names)

    def adapter_init1():
        global dir_exists, subdir_exists
        try: shutil.rmtree(DIRNAME)
        except OSError: pass
        return 1
    adapter_init1.func_code = aalmodel.setCodeFileLine(adapter_init1.func_code, '''examples\filesystemtest\filesystemtest.aal''', 15)
    adapter_init_list.append(adapter_init1)

    def adapter_exit1(verdict,reason):
        global dir_exists, subdir_exists
        if verdict == "pass" and dir_exists:
            log("cleaning up " + DIRNAME)
            shutil.rmtree(DIRNAME)
        pass
    adapter_exit1.func_code = aalmodel.setCodeFileLine(adapter_exit1.func_code, '''examples\filesystemtest\filesystemtest.aal''', 19)
    adapter_exit_list.append(adapter_exit1)

    action1name = "i:mkdir: ok"
    action1type = "input"
    def action1guard():
        global dir_exists, subdir_exists
        action_name = "i:mkdir: ok"
        input_name ="mkdir: ok"
        action_index = 0
        return not dir_exists
    action1guard.requires = []
    action1guard.func_code = aalmodel.setCodeFileLine(action1guard.func_code, '''examples\filesystemtest\filesystemtest.aal''', 21, "guard of action \"i:mkdir: ok\"")
    def action1body():
        global dir_exists, subdir_exists
        action_name = "i:mkdir: ok"
        input_name ="mkdir: ok"
        action_index = 0
        dir_exists = True
    action1body.func_code = aalmodel.setCodeFileLine(action1body.func_code, '''examples\filesystemtest\filesystemtest.aal''', 23, "body of action \"i:mkdir: ok\"")
    def action1adapter():
        global dir_exists, subdir_exists
        action_name = "i:mkdir: ok"
        input_name ="mkdir: ok"
        action_index = 0
        os.mkdir(DIRNAME)
        return 1
    action1adapter.func_code = aalmodel.setCodeFileLine(action1adapter.func_code, '''examples\filesystemtest\filesystemtest.aal''', 22, "adapter of action \"i:mkdir: ok\"")

    action2name = "i:rmdir: ok"
    action2type = "input"
    def action2guard():
        global dir_exists, subdir_exists
        action_name = "i:rmdir: ok"
        input_name ="rmdir: ok"
        action_index = 0
        return dir_exists and not subdir_exists
    action2guard.requires = []
    action2guard.func_code = aalmodel.setCodeFileLine(action2guard.func_code, '''examples\filesystemtest\filesystemtest.aal''', 26, "guard of action \"i:rmdir: ok\"")
    def action2body():
        global dir_exists, subdir_exists
        action_name = "i:rmdir: ok"
        input_name ="rmdir: ok"
        action_index = 0
        dir_exists = False
    action2body.func_code = aalmodel.setCodeFileLine(action2body.func_code, '''examples\filesystemtest\filesystemtest.aal''', 28, "body of action \"i:rmdir: ok\"")
    def action2adapter():
        global dir_exists, subdir_exists
        action_name = "i:rmdir: ok"
        input_name ="rmdir: ok"
        action_index = 0
        os.rmdir(DIRNAME)
        return 2
    action2adapter.func_code = aalmodel.setCodeFileLine(action2adapter.func_code, '''examples\filesystemtest\filesystemtest.aal''', 27, "adapter of action \"i:rmdir: ok\"")

    action3name = "i:mksubdir: ok"
    action3type = "input"
    def action3guard():
        global dir_exists, subdir_exists
        action_name = "i:mksubdir: ok"
        input_name ="mksubdir: ok"
        action_index = 0
        return dir_exists and not subdir_exists
    action3guard.requires = []
    action3guard.func_code = aalmodel.setCodeFileLine(action3guard.func_code, '''examples\filesystemtest\filesystemtest.aal''', 31, "guard of action \"i:mksubdir: ok\"")
    def action3body():
        global dir_exists, subdir_exists
        action_name = "i:mksubdir: ok"
        input_name ="mksubdir: ok"
        action_index = 0
        subdir_exists = True
    action3body.func_code = aalmodel.setCodeFileLine(action3body.func_code, '''examples\filesystemtest\filesystemtest.aal''', 33, "body of action \"i:mksubdir: ok\"")
    def action3adapter():
        global dir_exists, subdir_exists
        action_name = "i:mksubdir: ok"
        input_name ="mksubdir: ok"
        action_index = 0
        os.mkdir(SUBDIRNAME)
        return 3
    action3adapter.func_code = aalmodel.setCodeFileLine(action3adapter.func_code, '''examples\filesystemtest\filesystemtest.aal''', 32, "adapter of action \"i:mksubdir: ok\"")

    action4name = "i:rmsubdir: ok"
    action4type = "input"
    def action4guard():
        global dir_exists, subdir_exists
        action_name = "i:rmsubdir: ok"
        input_name ="rmsubdir: ok"
        action_index = 0
        return subdir_exists
    action4guard.requires = []
    action4guard.func_code = aalmodel.setCodeFileLine(action4guard.func_code, '''examples\filesystemtest\filesystemtest.aal''', 36, "guard of action \"i:rmsubdir: ok\"")
    def action4body():
        global dir_exists, subdir_exists
        action_name = "i:rmsubdir: ok"
        input_name ="rmsubdir: ok"
        action_index = 0
        subdir_exists = False
    action4body.func_code = aalmodel.setCodeFileLine(action4body.func_code, '''examples\filesystemtest\filesystemtest.aal''', 38, "body of action \"i:rmsubdir: ok\"")
    def action4adapter():
        global dir_exists, subdir_exists
        action_name = "i:rmsubdir: ok"
        input_name ="rmsubdir: ok"
        action_index = 0
        os.rmdir(SUBDIRNAME)
        return 4
    action4adapter.func_code = aalmodel.setCodeFileLine(action4adapter.func_code, '''examples\filesystemtest\filesystemtest.aal''', 37, "adapter of action \"i:rmsubdir: ok\"")

    action5name = "i:mkdir: already exists"
    action5type = "input"
    def action5guard():
        global dir_exists, subdir_exists
        action_name = "i:mkdir: already exists"
        input_name ="mkdir: already exists"
        action_index = 0
        return dir_exists
    action5guard.requires = []
    action5guard.func_code = aalmodel.setCodeFileLine(action5guard.func_code, '''examples\filesystemtest\filesystemtest.aal''', 41, "guard of action \"i:mkdir: already exists\"")
    def action5body():
        global dir_exists, subdir_exists
        action_name = "i:mkdir: already exists"
        input_name ="mkdir: already exists"
        action_index = 0
        pass
    def action5adapter():
        global dir_exists, subdir_exists
        action_name = "i:mkdir: already exists"
        input_name ="mkdir: already exists"
        action_index = 0
        try: os.mkdir(DIRNAME)
        except OSError, e:
            assert "File exists" in str(e), "Wrong exception: %s" % (e,)
            return
        assert False, "Exception expected"
        return 5
    action5adapter.func_code = aalmodel.setCodeFileLine(action5adapter.func_code, '''examples\filesystemtest\filesystemtest.aal''', 43, "adapter of action \"i:mkdir: already exists\"")

    action6name = "i:mksubdir: already exists"
    action6type = "input"
    def action6guard():
        global dir_exists, subdir_exists
        action_name = "i:mksubdir: already exists"
        input_name ="mksubdir: already exists"
        action_index = 0
        return subdir_exists
    action6guard.requires = []
    action6guard.func_code = aalmodel.setCodeFileLine(action6guard.func_code, '''examples\filesystemtest\filesystemtest.aal''', 51, "guard of action \"i:mksubdir: already exists\"")
    def action6body():
        global dir_exists, subdir_exists
        action_name = "i:mksubdir: already exists"
        input_name ="mksubdir: already exists"
        action_index = 0
        pass
    def action6adapter():
        global dir_exists, subdir_exists
        action_name = "i:mksubdir: already exists"
        input_name ="mksubdir: already exists"
        action_index = 0
        try: os.mkdir(SUBDIRNAME)
        except OSError, e:
            assert "File exists" in str(e), "Wrong exception: %s" % (e,)
            return
        assert False, "Exception expected"
        return 6
    action6adapter.func_code = aalmodel.setCodeFileLine(action6adapter.func_code, '''examples\filesystemtest\filesystemtest.aal''', 53, "adapter of action \"i:mksubdir: already exists\"")

    action7name = "i:rmdir: no such file"
    action7type = "input"
    def action7guard():
        global dir_exists, subdir_exists
        action_name = "i:rmdir: no such file"
        input_name ="rmdir: no such file"
        action_index = 0
        return not dir_exists
    action7guard.requires = []
    action7guard.func_code = aalmodel.setCodeFileLine(action7guard.func_code, '''examples\filesystemtest\filesystemtest.aal''', 61, "guard of action \"i:rmdir: no such file\"")
    def action7body():
        global dir_exists, subdir_exists
        action_name = "i:rmdir: no such file"
        input_name ="rmdir: no such file"
        action_index = 0
        pass
    def action7adapter():
        global dir_exists, subdir_exists
        action_name = "i:rmdir: no such file"
        input_name ="rmdir: no such file"
        action_index = 0
        try: os.rmdir(DIRNAME)
        except OSError, e:
            assert "No such file" in str(e), "Wrong exception %s" % (e,)
            return
        assert False, "Exception expected"
        return 7
    action7adapter.func_code = aalmodel.setCodeFileLine(action7adapter.func_code, '''examples\filesystemtest\filesystemtest.aal''', 63, "adapter of action \"i:rmdir: no such file\"")

    action8name = "i:rmdir: not empty"
    action8type = "input"
    def action8guard():
        global dir_exists, subdir_exists
        action_name = "i:rmdir: not empty"
        input_name ="rmdir: not empty"
        action_index = 0
        return subdir_exists
    action8guard.requires = []
    action8guard.func_code = aalmodel.setCodeFileLine(action8guard.func_code, '''examples\filesystemtest\filesystemtest.aal''', 71, "guard of action \"i:rmdir: not empty\"")
    def action8body():
        global dir_exists, subdir_exists
        action_name = "i:rmdir: not empty"
        input_name ="rmdir: not empty"
        action_index = 0
        pass
    def action8adapter():
        global dir_exists, subdir_exists
        action_name = "i:rmdir: not empty"
        input_name ="rmdir: not empty"
        action_index = 0
        try: os.rmdir(DIRNAME)
        except OSError, e:
            assert "not empty" in str(e), "Wrong exception: %s" % (e,)
            return
        assert False, "Exception expected"
        return 8
    action8adapter.func_code = aalmodel.setCodeFileLine(action8adapter.func_code, '''examples\filesystemtest\filesystemtest.aal''', 73, "adapter of action \"i:rmdir: not empty\"")

    action9name = "i:rmsubdir: no such file"
    action9type = "input"
    def action9guard():
        global dir_exists, subdir_exists
        action_name = "i:rmsubdir: no such file"
        input_name ="rmsubdir: no such file"
        action_index = 0
        return not subdir_exists
    action9guard.requires = []
    action9guard.func_code = aalmodel.setCodeFileLine(action9guard.func_code, '''examples\filesystemtest\filesystemtest.aal''', 81, "guard of action \"i:rmsubdir: no such file\"")
    def action9body():
        global dir_exists, subdir_exists
        action_name = "i:rmsubdir: no such file"
        input_name ="rmsubdir: no such file"
        action_index = 0
        pass
    def action9adapter():
        global dir_exists, subdir_exists
        action_name = "i:rmsubdir: no such file"
        input_name ="rmsubdir: no such file"
        action_index = 0
        try: os.rmdir(SUBDIRNAME)
        except OSError, e:
            assert "No such file" in str(e), "Wrong exception %s" % (e,)
            return
        assert False, "Exception expected"
        return 9
    action9adapter.func_code = aalmodel.setCodeFileLine(action9adapter.func_code, '''examples\filesystemtest\filesystemtest.aal''', 83, "adapter of action \"i:rmsubdir: no such file\"")

    tag1name = "dir exists"
    def tag1guard():
        global dir_exists, subdir_exists
        tag_name = "dir exists"
        return dir_exists
    tag1guard.requires=[]
    tag1guard.func_code = aalmodel.setCodeFileLine(tag1guard.func_code, '''examples\filesystemtest\filesystemtest.aal''', 94, "guard of tag \"dir exists\"")
    def tag1adapter():
        global dir_exists, subdir_exists
        tag_name = "dir exists"
        assert os.access(DIRNAME, os.R_OK), "%s not accessible" % (DIRNAME,)
    tag1adapter.func_code = aalmodel.setCodeFileLine(tag1adapter.func_code, '''examples\filesystemtest\filesystemtest.aal''', 95, "adapter of tag \"dir exists\"")

    tag2name = "no dir"
    def tag2guard():
        global dir_exists, subdir_exists
        tag_name = "no dir"
        return not dir_exists
    tag2guard.requires=[]
    tag2guard.func_code = aalmodel.setCodeFileLine(tag2guard.func_code, '''examples\filesystemtest\filesystemtest.aal''', 98, "guard of tag \"no dir\"")
    def tag2adapter():
        global dir_exists, subdir_exists
        tag_name = "no dir"
        assert not os.access(DIRNAME, os.R_OK), "%s accessible" % (DIRNAME,)
    tag2adapter.func_code = aalmodel.setCodeFileLine(tag2adapter.func_code, '''examples\filesystemtest\filesystemtest.aal''', 99, "adapter of tag \"no dir\"")

    tag3name = "subdir exists"
    def tag3guard():
        global dir_exists, subdir_exists
        tag_name = "subdir exists"
        return subdir_exists
    tag3guard.requires=[]
    tag3guard.func_code = aalmodel.setCodeFileLine(tag3guard.func_code, '''examples\filesystemtest\filesystemtest.aal''', 102, "guard of tag \"subdir exists\"")
    def tag3adapter():
        global dir_exists, subdir_exists
        tag_name = "subdir exists"
        assert os.access(SUBDIRNAME, os.R_OK), "%s not accessible" % (SUBDIRNAME,)
    tag3adapter.func_code = aalmodel.setCodeFileLine(tag3adapter.func_code, '''examples\filesystemtest\filesystemtest.aal''', 103, "adapter of tag \"subdir exists\"")

    tag4name = "no subdir"
    def tag4guard():
        global dir_exists, subdir_exists
        tag_name = "no subdir"
        return not subdir_exists
    tag4guard.requires=[]
    tag4guard.func_code = aalmodel.setCodeFileLine(tag4guard.func_code, '''examples\filesystemtest\filesystemtest.aal''', 106, "guard of tag \"no subdir\"")
    def tag4adapter():
        global dir_exists, subdir_exists
        tag_name = "no subdir"
        assert not os.access(SUBDIRNAME, os.R_OK), "%s accessible" % (SUBDIRNAME,)
    tag4adapter.func_code = aalmodel.setCodeFileLine(tag4adapter.func_code, '''examples\filesystemtest\filesystemtest.aal''', 107, "adapter of tag \"no subdir\"")
    def adapter_init():
        for x in _gen_filesystemtest.adapter_init_list:
            ret = x()
            if not ret and ret != None:
                return ret
        return True
    def initial_state():
        for x in _gen_filesystemtest.initial_state_list:
            ret = x()
            if not ret and ret != None:
                return ret
        return True
    def adapter_exit(verdict,reason):
        for x in _gen_filesystemtest.adapter_exit_list:
            ret = x(verdict,reason)
            if not ret and ret != None:
                return ret
        return True

Model = _gen_filesystemtest
