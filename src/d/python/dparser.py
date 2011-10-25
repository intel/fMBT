# Copyright (c) 2003, 2004 Brian Sabbey
# contributions by Milosz Krajewski
# contributions by John Plevyak

import sys, types, os, hashlib, dparser_swigc, string 

class user_pyobjectsPtr :
    def __init__(self,this):
        self.this = this
        self.thisown = 0
    def __setattr__(self,name,value):
        if name == "t" :
            self.this.__setattr__(name, value)
            return
        self.__dict__[name] = value
    def __getattr__(self,name):
        if name == "t" : 
            return self.this.__getattr__(name)
        raise AttributeError,name
    def __repr__(self):
        return "<C user_pyobjects instance>"
    
class user_pyobjects(user_pyobjectsPtr):
    def __init__(self,this):
        self.this = this

class d_loc_tPtr :
    def __init__(self, this, d_parser):
        self.this = this
        self.thisown = 0
        self.d_parser = d_parser
    def __setattr__(self, name, value):
        if name == "s" :
            dparser_swigc.my_d_loc_t_s_set(self.this,self.d_parser,value)
        elif name in ["pathname", "previous_col", "col", "line", "ws"]:
            self.this.__setattr__(name, value)     
        else:
            self.__dict__[name] = value
        
    def __getattr__(self, name):
        if name == "s" : 
            return dparser_swigc.my_d_loc_t_s_get(self.this,self.d_parser)
        elif name in ["pathname", "previous_col", "col", "line", "ws"]:
            return self.this.__getattr__(name)
        raise AttributeError,name

    def __repr__(self):
        return "<C d_loc_t instance>"
    
    
class d_loc_t(d_loc_tPtr):
    def __init__(self, this, d_parser, buf):
        self.this = this
        self.d_parser = d_parser
        self.buf = buf
        
class D_ParseNodePtr :
    def __init__(self, this):
        self.this = this
        self.thisown = 0
    def __setattr__(self, name, value):
        if name == "end_skip" :
            dparser_swigc.my_D_ParseNode_end_skip_set(self.this,self.d_parser,value)
        elif name == "end" :
            dparser_swigc.my_D_ParseNode_end_set(self.this,self.d_parser,value)
        elif name in ["start_loc", "globals", "user"]:
            self.this.__setattr__(name, value)
        else:
            self.__dict__[name] = value
        
    def __getattr__(self, name):
        if name == "symbol" : 
            return dparser_swigc.my_D_ParseNode_symbol_get(self.this,self.d_parser).decode('string_escape')
        elif name == "end" : 
            return dparser_swigc.my_D_ParseNode_end_get(self.this,self.d_parser)
        elif name == "end_skip" : 
            return dparser_swigc.my_D_ParseNode_end_skip_get(self.this,self.d_parser)
        elif name == "globals" : 
            return self.this.__getattr__(name)
        elif name == "number_of_children":
            return dparser_swigc.d_get_number_of_children(self.this)
        elif name == "user" : 
            return user_pyobjectsPtr(self.this.__getattr__(name))
        elif name == "start_loc" :
            val = self.__dict__.get(name)
            if not val:
                val = self.__dict__[name] = d_loc_t(self.this.start_loc, self.d_parser, self.buf)
            return val
        if name == "c":
            val = self.__dict__.get(name, None)
            if not val:
                nc = dparser_swigc.d_get_number_of_children(self.this)
                val = self.__dict__[name] = [None]*nc
                for i in range(0, nc):
                    val[i] = D_ParseNode(dparser_swigc.d_get_child(self.this, i), self.d_parser, self.buf)
            return val
        raise AttributeError,name
        
    def __repr__(self):
        return "<C D_ParseNode instance>"
    
class D_ParseNode(D_ParseNodePtr):
    def __del__(self):
        dparser_swigc.remove_parse_tree_viewer(self.d_parser)
    def __init__(self, this, d_parser, buf):
        self.this = this
        self.d_parser = d_parser
        self.buf = buf
        dparser_swigc.add_parse_tree_viewer(self.d_parser)

class Reject: pass

class SyntaxError(Exception):
    pass
class AmbiguityException(Exception):
    pass

def my_syntax_error_func(loc):
    ee = '...'
    be = '...'
    width = 25
    mn = loc.s - width
    if mn < 0:
        mn = 0
        be = ''
    mx = loc.s + 25
    if mx > len(loc.buf):
        mx = len(loc.buf)
        ee = ''
    begin = loc.buf[mn:loc.s]
    end = loc.buf[loc.s:mx]
    string = '\n\nsyntax error, line:' + str(loc.line) + '\n\n' + be + begin +  '[syntax error]' + end + ee + '\n'
    raise SyntaxError, string

def my_ambiguity_func(nodes):
    raise AmbiguityException, "\nunresolved ambiguity.  Symbols:\n" + string.join([node.symbol for node in nodes], "\n")

class Tables:
    def __init__(self):
        self.sig = hashlib.md5();
        self.sig.update('1.15')
        self.tables = None
        
    def __del__(self):
        del self.sig
        if self.tables:
            dparser_swigc.unload_parser_tables(self.tables)
        
    def update(self,data):
        self.sig.update(data)
        
    def sig_changed(self, filename):
        try:
            sig_file = open(filename + ".md5", "rb")
            line = sig_file.read()
            sig_file.close()
            if line == self.sig.digest():
                return 0
        except IOError, SyntaxError:
            pass
        return 1
        
    def load_tables(self,grammar_str, filename, make_grammar_file):
        if make_grammar_file:
            g_file = open(filename, "wb") # 'binary' mode has been set to force \n on end of the line
            g_file.write(grammar_str)
            g_file.close()
            
        if self.sig_changed(filename):
            dparser_swigc.make_tables(grammar_str, filename)
            sig_file = open(filename + ".md5", "wb")
            sig_file.write(self.sig.digest())
            sig_file.close()

        if self.tables:
            dparser_swigc.unload_parser_tables(self.tables)
        self.tables = dparser_swigc.load_parser_tables(filename + ".d_parser.dat")
     
    def getTables(self):
        return self.tables
        
class ParsingException(Exception):
    pass
    
class Parser:
    def __init__(self, modules=None, parser_folder=None, file_prefix="d_parser_mach_gen",make_grammar_file=0):
        self.tables = Tables()
        self.actions = []
        if not modules:
            try:
                raise RuntimeError
            except RuntimeError:
                e,b,t = sys.exc_info()
            
            dicts = [t.tb_frame.f_back.f_globals]
        else:
            if isinstance(modules, list):
                dicts = [module.__dict__ for module in modules]
            elif isinstance(modules, dict):
                dicts = [modules]
            else:
                dicts = [modules.__dict__]
                
        functions = []
        for dictionary in dicts:
            f = [val for name, val in dictionary.items() 
                 if (isinstance(val, types.FunctionType)) and name[0:2] == 'd_']
            f.sort(lambda x, y: cmp(x.func_code.co_filename, y.func_code.co_filename) or cmp(x.func_code.co_firstlineno, y.func_code.co_firstlineno))
            functions.extend(f)
        if len(functions) == 0:
            raise "\nno actions found.  Action names must start with 'd_'"
            
        if parser_folder == None:
            parser_folder = os.path.dirname(sys.argv[0])
            if len(parser_folder) == 0:
                 parser_folder = os.getcwd()
            parser_folder = string.replace(parser_folder, '\\', '/')
            
        self.filename = os.path.join(parser_folder, file_prefix + ".g")
        
        grammar_str = []
        self.takes_strings = 0
        self.takes_globals = 0
        for f in functions:
            if f.__doc__:
                grammar_str.append(f.__doc__) 
                self.tables.update(f.__doc__)
            else:
                raise "\naction missing doc string:\n\t" + f.__name__
            grammar_str.append(" ${action};\n")
            if f.func_code.co_argcount == 0:
                raise "\naction " + f.__name__ + " must take at least one argument\n"
            speculative = 0
            arg_types = [0]
            for i in range(1, f.func_code.co_argcount):
                var = f.func_code.co_varnames[i]
                if var == 'spec':
                    arg_types.append(1)
                    speculative = 1
                elif var == 'g':
                    arg_types.append(2)
                    self.takes_globals = 1
                elif var == 's':
                    arg_types.append(3)
                    self.takes_strings = 1
                elif var == 'nodes':
                    arg_types.append(4)
                elif var == 'this':
                    arg_types.append(5)
                elif var == 'spec_only':
                    arg_types.append(6)
                    speculative = -1
                elif var == 'parser':
                    arg_types.append(7)
                else:
                    raise "\nunknown argument name:\n\t" + var + "\nin function:\n\t" + f.__name__
            self.actions.append((f, arg_types, speculative))
        grammar_str = string.join(grammar_str, '')
        
        self.tables.load_tables(grammar_str, self.filename, make_grammar_file)

    def parse(self, buf, buf_offset=0,
              initial_skip_space_fn=None,
              syntax_error_fn=my_syntax_error_func, ambiguity_fn=my_ambiguity_func,
              make_token=None,
              dont_fixup_internal_productions=0,
			  fixup_EBNF_productions=0,
              dont_merge_epsilon_trees=0,
              commit_actions_interval=100,
              error_recovery=0,
              print_debug_info=0,
              partial_parses=0,
              dont_compare_stacks=0,
              dont_use_greediness_for_disambiguation=0,
              dont_use_height_for_disambiguation=0,
              start_symbol=''):
                  
        if not isinstance(buf, basestring):
            raise ParsingException("Message to parse is not a string: %r" % buf)
                  
        parser = dparser_swigc.make_parser(self.tables.getTables(), self, Reject, make_token, d_loc_t, D_ParseNode,
                                           self.actions, initial_skip_space_fn, syntax_error_fn,
                                           ambiguity_fn,
                                           dont_fixup_internal_productions, fixup_EBNF_productions,
                                           dont_merge_epsilon_trees,
                                           commit_actions_interval,
                                           error_recovery,
                                           print_debug_info,
                                           partial_parses,
                                           dont_compare_stacks,
                                           dont_use_greediness_for_disambiguation,
                                           dont_use_height_for_disambiguation,
                                           start_symbol, self.takes_strings, self.takes_globals)
        result = dparser_swigc.run_parser(parser, buf, buf_offset)
        return ParsedStructure(result)
        
class ParsedStructure:
    def __init__(self,result):
        self.stringLeft = ""
        self.structure = None
        self.top_node = None
        if result:
            if len(result) == 3:
                self.stringLeft = result[2]
            node = result[1]
            self.top_node = node #D_ParseNode(node.this, node.d_parser, node.buf)
            self.structure = result[0]
        
    def getStructure(self):
        return self.structure
    
    def getStringLeft(self):
        return self.stringLeft
		
