/*
 * fMBT, free Model Based Testing tool
 * Copyright (c) 2011, Intel Corporation.
 *
 * This program is free software; you can redistribute it and/or modify it
 * under the terms and conditions of the GNU Lesser General Public License,
 * version 2.1, as published by the Free Software Foundation.
 *
 * This program is distributed in the hope it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for
 * more details.
 *
 * You should have received a copy of the GNU Lesser General Public License along with
 * this program; if not, write to the Free Software Foundation, Inc.,
 * 51 Franklin St - Fifth Floor, Boston, MA 02110-1301 USA.
 *
 *
 */

#include "aalang_py.hh"
#include "helper.hh"

std::string to_list(std::list<std::string>& l) {
  if (l.begin()==l.end()) {
    return "";
  }
  std::string ret="\"" +  l.back() + "\"";
  return ret;
}

std::string indent(int depth, const std::string &s)
{
  std::string rv;

  int offset = 0; // original indentation
  int first_linebreak = s.find('\n');
  int first_nonspace = s.find_first_not_of(" \t\n\r");
  int line_start = 0;
  int line_end = 0;

  /* search the first non-empty line, the indentation offset is
   * calculated based on that. */
  while (first_linebreak < first_nonspace) {
    line_start = first_linebreak + 1;
    first_linebreak = s.find('\n', first_linebreak + 1);
    if (first_linebreak == (int)s.npos) first_linebreak = s.length() - 1;
  }
  offset = first_nonspace - line_start;

  do {
    line_end = s.find('\n', line_start);
    if (line_end == (int)s.npos) line_end = s.length() - 1;
    if (offset > depth) {
      // orig indentation is too deep, cut off (depth - offset)
      // spaces
      if (line_end - line_start > offset - depth) {
        rv += s.substr(line_start + offset - depth,
                       line_end - line_start - offset + depth + 1);
      } else {
        // there is not enough spaces to cut
        rv += "\n";
      }
    } else {
      // orig indentation is too shallow, add (depth - offset) spaces
      for (int i = 0; i < depth - offset; i++) rv += " ";
      rv += s.substr(line_start, line_end - line_start + 1);
    }
    line_start = line_end + 1;
  } while (line_end < (int)s.length() - 1);

  // right-strip
  rv.erase(rv.find_last_not_of(" \t\n\r")+1);

  return rv;
}

std::string python_lineno_wrapper(const std::string& filename,int lineno,
                                  const std::string& funcname,int trim,int ind,
                                  const std::string& human=")")
{
  if (lineno) {
    return indent(ind,funcname + ".func_code = aalmodel.setCodeFileLine(" +
                  funcname + ".func_code, '''" + filename + "''', " +
                  to_string(lineno-trim) + human ) + "\n";
  }
  return "";
}

std::string python_lineno_wrapper(const codefileline& cfl,
                                  const std::string& funcname,int trim,int ind,
                                  const std::string& human=")")
{
  return python_lineno_wrapper(cfl.second.first,cfl.second.second,funcname,
                               trim,ind,human);
}

std::string aalang_py::action_helper(const codefileline& cfl,std::string s,
				     std::string& funcname,int i,std::string& acnt)
{
  funcname = "action" + acnt + s;
  std::string extra_name;
  if (action_name_type == aalang::IACT)
      extra_name = "input_name =\"" + multiname[i].first.substr(2) + "\"";
  else if (action_name_type == aalang::OBSERVE)
      extra_name = "output_name =\"" + multiname[i].first.substr(2)  + "\"";


  return "    def " + funcname + "():\n" + variables
    +    "        action_name = \"" + multiname[i].first + "\"\n"
    +    "        " + extra_name + "\n"
    +    "        action_index = " + to_string(i) + "\n"
    +    indent(8,cfl.first)+"\n";
}

const std::string aalang_py::class_name() const
{
  return "_gen_" + *name;
}

const std::string aalang_py::serialN(const std::string postfix, bool cls) const
{
  // returns [cls.]serial(currentblock)<postfix>
  std::string full_name = "serial" + to_string(abs(serial_stack.back())) + postfix;
  if (cls) return class_name() + "." + full_name;
  else return full_name;
}

const std::string aalang_py::serialN_1(const std::string postfix, bool cls) const
{
  // returns [cls.]serial(outerblock "N-1")<postfix>
  std::list<int>::const_iterator outer_serial = serial_stack.end();
  --outer_serial; --outer_serial;
  std::string full_name = "serial" + to_string(abs(*outer_serial)) + postfix;
  if (cls) return class_name() + "." + full_name;
  else return full_name;
}

const int aalang_py::serial_stackN_1() const
{
  std::list<int>::const_iterator outer_serial = serial_stack.end();
  --outer_serial; --outer_serial;
  return *outer_serial;
}

void default_if_empty(std::string& s, const std::string& default_value)
{
  size_t first_nonspace = s.find_first_not_of(" \t\n\r");
  if (first_nonspace == std::string::npos) s = default_value;
}

void aalang_py::set_starter(std::string* st,const char* file,int line,int col)
{
  s+=indent(0, *st)+"\n";
  delete st;
}


void aalang_py::set_name(std::string* name,bool first,ANAMETYPE t)
{
  if (first) {
    ma_save.push(m_guard);
    ma_save.push(m_body);
    ma_save.push(m_adapter);
    ma_stack.push_back(multiname);
    ta_stack.push_back(tag);
    ta_stack.push_back(adapter);
    multiname.clear();
    tag = false;
    adapter = false;
    serial_stack.push_back(0); // inside action block
  }

  action_name_type = t;

  multiname.push_back(std::pair<std::string,int>(*name,action_cnt));
  action_cnt++;

  if (first) {
    guard_requires.push_back("action"+to_string(action_cnt-1)+"guard");
  }

  delete name;

}

aalang_py::~aalang_py()
{
  if (name)
    delete name;
}

void aalang_py::set_namestr(std::string* _name)
{
  name=_name;
  s+="import aalmodel\n"
    "class " + class_name() + "(aalmodel.AALModel):\n"
    "    def __init__(self):\n"
    "        aalmodel.AALModel.__init__(self, globals())\n";
  s+="    adapter_init_list = []\n";
  s+="    initial_state_list = []\n";
  s+="    adapter_exit_list = []\n";
  s+="    push_variables_set = set()\n";
}

void aalang_py::set_variables(std::string* var,const char* file,int line,int col)
{
  std::string ivar = indent(0,*var);
  if (ivar!="") {
    variables+="        global " + indent(0,*var) + "\n";
  }
  m_lines_in_vars = std::count(variables.begin(), variables.end(), '\n');
  delete var;
}

void aalang_py::set_istate(std::string* ist,const char* file,int line,int col)
{
  model_init_counter++;
  const std::string funcname("initial_state"+to_string(model_init_counter));
  s += "\n    def " + funcname + "():\n" + variables +
    indent(8, *ist) + "\n" +
    indent(8, "pass") + "\n";
  s += python_lineno_wrapper(file,line,funcname,1+m_lines_in_vars,4);
  s += indent(4,"initial_state_list.append("+funcname+")")+"\n";
  s += indent(4,"push_variables_set.update("+funcname+".func_code.co_names)")+"\n";
  delete ist;
}

void aalang_py::set_ainit(std::string* iai,const char* file,int line,int col)
{
  adapter_init_counter++;
  const std::string r("return 1");
  const std::string funcname("adapter_init"+to_string(adapter_init_counter));
  s += "\n    def " + funcname + "():\n" + variables +
    indent(8, *iai) + "\n" + indent(8, r) + "\n";
  s += python_lineno_wrapper(file,line,funcname,1+m_lines_in_vars,4);

  s += indent(4,"adapter_init_list.append("+funcname+")")+"\n";
  delete iai;
}

void aalang_py::set_aexit(std::string* iai,const char* file,int line,int col)
{
  adapter_exit_counter++;
  const std::string funcname("adapter_exit"+to_string(adapter_exit_counter));
  s += "\n    def " + funcname + "(verdict,reason):\n" + variables +
    indent(8, *iai) + "\n" + indent(8, "pass\n") + "\n";
  s += python_lineno_wrapper(file,line,funcname,1+m_lines_in_vars,4);

  s += indent(4,"adapter_exit_list.append("+funcname+")")+"\n";
  delete iai;
}

void aalang_py::set_tagname(std::string* name,bool first)
{
  if (first) {
    ma_save.push(m_guard);
    ma_save.push(m_body);
    ma_save.push(m_adapter);
    ma_stack.push_back(multiname);
    ta_stack.push_back(tag);
    ta_stack.push_back(adapter);
    multiname.clear();
    tag = true;
    adapter = false;
  }

  multiname.push_back(std::pair<std::string,int>(*name,tag_cnt));
  tag_cnt++;

  if (first) {
    guard_requires.push_back("tag"+to_string(tag_cnt-1)+"guard");
  }

  delete name;
}

void aalang_py::next_tag()
{
  std::string tcnt;
  guard_requires.pop_back();

  requires = to_list(guard_requires);

  for (unsigned int i = 0; i < multiname.size(); i++) {
    tcnt=to_string(multiname[i].second);

    s+="\n    tag" + tcnt + "name = \""+multiname[i].first+"\"\n";
    /* tagXguard */
    const std::string funcname("tag" + tcnt + "guard");
    s+="    def " + funcname + "():\n" + variables;
    s+="        tag_name = \"" + multiname[i].first + "\"\n";
    s+=indent(8,m_guard.first)+"\n";

    // tag?guard.requires=[...];
    s+="    tag" + tcnt + "guard.requires=[" + requires + "]\n";

    s+=python_lineno_wrapper(m_guard,funcname,2+m_lines_in_vars,4,
                             ", \"guard of tag \\\"" + multiname[i].first
                             + "\\\"\")");

    if (adapter) {
      const std::string funcname("tag" + tcnt + "adapter");

      s+="    def " + funcname + "():\n" + variables;
      s+="        tag_name = \"" + multiname[i].first + "\"\n";
      s+=indent(8,m_adapter.first)+"\n";

      s+=python_lineno_wrapper(m_adapter,funcname,2+m_lines_in_vars,4,
			       ", \"adapter of tag \\\"" + multiname[i].first
			       + "\\\"\")");
    }
    /*
    tag_cnt++;
    tcnt=to_string(tag_cnt);
    */
  }
  multiname.clear();
  adapter = ta_stack.back(); ta_stack.pop_back();
  tag =  ta_stack.back(); ta_stack.pop_back();
  multiname = ma_stack.back(); ma_stack.pop_back();

  m_adapter=ma_save.top();ma_save.pop();
  m_body   =ma_save.top();ma_save.pop();
  m_guard  =ma_save.top();ma_save.pop();
}

void aalang_py::set_guard(std::string* gua,const char* file,int line,int col)
{
  std::string tmp=*gua;
  if (gua!=&default_guard)
    delete gua;
  default_if_empty(tmp, "return True");
  m_guard = codefileline(tmp,fileline(file,line));
}

void aalang_py::parallel(bool start,std::list<std::string>* __params) {
  bool single=false;

  /* debug... print params  */
  if (__params) {
    std::list<std::string>::iterator b=
      __params->begin();
    std::list<std::string>::iterator e=
      __params->end();

    for(std::list<std::string>::iterator i=b;i!=e;i++) {
      if (*i == "single") {
	single=true;
      }
    }
  } else {
  }

  if (start) {
    serial_stack.push_back(-serial_cnt); // parallel is negative
    std::string sNg =
    s += "\n"
      "    " + serialN("name") + " = \"" + serialN("") + "\"\n"
      "    def " + serialN("guard") + "():\n"
      "        return guard_list[-2] in " + serialN("guard", true) +
      "_next_block\n"
      "    " + serialN("guard") + ".blocks = []\n"
      "    " + serialN("guard") + "_next_block = set()\n"
      "    def " + serialN("step") + "(self, upper):\n"
      "        " + serialN("guard", true) + "_next_block.remove("
      "upper)\n"
      "        if not " + serialN("guard", true) + "_next_block:\n" +
      "            " + serialN("guard", true) + "_next_block";

    if (single) {
      s += " = set()\n";
    } else {
      s += " = set(" + serialN("guard", true) + ".blocks)\n";
    }
    if (serial_stack.size() > 1 && serial_stack.back() != 0) {
      // nested block:
      // - if all subblocks were executed, notify outer block
      // - executing subblocks requires outer block permission.
      s +=
        "        if len(" + serialN("guard", true) + "_next_block) == len(" +
        serialN("guard", true) + ".blocks):\n"
        "            self." + serialN_1("step") + "(\"" + serialN("") + "\")\n"
        "    " + serialN("guard") + ".requires = [\"" + serialN_1("guard") +
        "\"]\n"
        "    " + serialN_1("guard") + ".blocks.append(\"" +
        serialN("") + "\")\n"
        ;

      if (serial_stackN_1() > 0) {
        // parallel is inside serial block
        s += "    " + serialN_1("guard") + "_next_block.insert(0, \"" +
          serialN("") + "\")\n";

      } else {
        // parallel is inside parallel block
        s += "    " + serialN_1("guard") + "_next_block.add(\"" +
          serialN("") + "\")\n";
      }
    }
    serial_cnt += 1;
  } else {
    serial_stack.pop_back();
  }
}

void aalang_py::serial(bool start,std::list<std::string>* __params) {

  bool single=false;

  /* debug... print params  */
  if (__params) {
    std::list<std::string>::iterator b=
      __params->begin();
    std::list<std::string>::iterator e=
      __params->end();

    for(std::list<std::string>::iterator i=b;i!=e;i++) {
      if (*i == "single") {
	single=true;
      }
    }
  } else {
  }
  if (start) {
    serial_stack.push_back(serial_cnt);
    s += "\n"
      "    " + serialN("name") + " = \"" + serialN("") + "\"\n"
      "    def " + serialN("guard") + "():\n"
      "        return " + serialN("guard", true) +
      "_next_block[-1] == guard_list[-2]\n"
      "    " + serialN("guard") + ".blocks = []\n"
      "    " + serialN("guard") + "_next_block = []\n"
      "    def " + serialN("step") + "(self, upper):\n"
      "        " + serialN("guard", true) + "_next_block.pop()\n"
      "        if not " + serialN("guard", true) + "_next_block:\n"
      "            " + serialN("guard", true) + "_next_block";
    if (single) {
      s += ".append(None)\n";
    } else {
      s += " = " + serialN("guard", true) + ".blocks[::-1]\n";
    }
    if (serial_stack.size() > 1 && serial_stack.back() != 0) {
      // nested block:
      // - if all subblocks were executed, notify outer block
      // - executing subblocks requires outer block permission.
      s +=
        "            self." + serialN_1("step") + "(\"" + serialN("") + "\")\n"
        "    " + serialN("guard") + ".requires = [\"" + serialN_1("guard") +
        "\"]\n"
        "    " + serialN_1("guard") + ".blocks.append(\"" + serialN("")+"\")\n"
        ;

      if (serial_stackN_1() > 0) {
        // serial inside serial block
        s += "    " + serialN_1("guard") + "_next_block.insert(0, \"" +
          serialN("") + "\")\n";
      } else {
        // serial inside parallel block
        s += "    " + serialN_1("guard") + "_next_block.add(\"" +
          serialN("") + "\")\n";
      }
    }
    serial_cnt += 1;
  } else {
    serial_stack.pop_back();
  }
}

void aalang_py::set_push(std::string* p,const char* file,int line,int col)
{
  push=*p;
  delete p;
}

void aalang_py::set_pop(std::string* p,const char* file,int line,int col)
{
  pop=*p;
  delete p;
}

void aalang_py::set_body(std::string* bod,const char* file,int line,int col)
{
  std::string tmp=*bod;
  if (bod!=&default_body)
    delete bod;
  default_if_empty(tmp, "pass");
  m_body = codefileline(tmp,fileline(file,line));
}

void aalang_py::set_adapter(std::string* ada,const char* file,int line,int col)
{
  adapter = true;
  std::string tmp=*ada;
  if (ada!=&default_adapter)
    delete ada;
  default_if_empty(tmp, "pass");
  m_adapter = codefileline(tmp,fileline(file,line));
}

void aalang_py::next_action()
{
  std::string acnt;
  guard_requires.pop_back();
  serial_stack.pop_back();
  requires = to_list(guard_requires);

  for (unsigned int i = 0; i < multiname.size(); i++) {
    std::string funcname;
    acnt = to_string(multiname[i].second);

    /* actionXname, actionXtype */
    s+="\n    action" + acnt + "name = \"" + multiname[i].first + "\"\n"
      +"    action" + acnt + "type = ";
    if (multiname[i].first.size() > 0 && multiname[i].first.c_str()[0] == 'o') {
      s += "\"output\"\n";
      this_is_input = false;
    } else {
      s += "\"input\"\n";
      this_is_input = true;
    }

    if (!serial_stack.empty() && serial_stack.back() != 0) {
      s += "    " + serialN("guard") + ".blocks.append(\"" + multiname[i].first + "\")\n";
      if (serial_stack.back() > 0) {
        // action is inside serial block
        s += "    " + serialN("guard") + "_next_block.insert(0, \"" + multiname[i].first + "\")\n";

      } else if (serial_stack.back() < 0) {
        // action is inside parallel block
        s += "    " + serialN("guard") + "_next_block.add(\"" + multiname[i].first + "\")\n";
      }
    }
    /* actionXguard */

    s+=action_helper(m_guard,"guard",funcname,i,acnt);

    // action + acnt + guard.requires=[...];
    s+="    action" + acnt + "guard.requires = [" + requires + "]\n";
    if (!serial_stack.empty() && serial_stack.back() != 0) {
      s+="    action" + acnt + "guard.requires += [\"" + serialN("guard") + "\"]\n";
    }

    s+=python_lineno_wrapper(m_guard,funcname,4+m_lines_in_vars,4,
                             ", \"guard of action \\\"" + multiname[i].first +
                             "\\\"\")");

    /* actionXbody */
    s+=action_helper(m_body,"body",funcname,i,acnt);
    s+=python_lineno_wrapper(m_body,funcname,4+m_lines_in_vars,4,
                             ", \"body of action \\\"" + multiname[i].first +
                             "\\\"\")");
    if (!serial_stack.empty() && serial_stack.back() != 0) {
      s += "    action" + acnt + "body_postcall = [\""
        + serialN("step") + "\"]\n";
    }
    /* actionXadapter */
    s+=action_helper(m_adapter,"adapter",funcname,i,acnt);
    if (this_is_input) {
      s+="        return " +acnt + "\n";
    } else {
      s+="        return False\n";
    }
    s+=python_lineno_wrapper(m_adapter,funcname,4+m_lines_in_vars,4,
                             ", \"adapter of action \\\"" + multiname[i].first
                             + "\\\"\")");
    /*
    action_cnt++;
    acnt=to_string(action_cnt);
    */
  }
  multiname.clear();

  adapter = ta_stack.back(); ta_stack.pop_back();
  tag =  ta_stack.back(); ta_stack.pop_back();
  multiname = ma_stack.back(); ma_stack.pop_back();

  m_adapter=ma_save.top();ma_save.pop();
  m_body   =ma_save.top();ma_save.pop();
  m_guard  =ma_save.top();ma_save.pop();
}

std::string aalang_py::stringify()
{
  s += indent(4,"\n    def adapter_init():\n") + "\n" +
    indent(8,"for x in "+class_name()+".adapter_init_list:\n"
	   "    ret = x()\n"
	   "    if not ret and ret != None:\n"
	   "        return ret\n"
	   "return True\n") + "\n" +
    indent(4,"\n    def initial_state():\n") + "\n" +
    indent(8,"for x in "+class_name()+".initial_state_list:\n"
	   "    ret = x()\n"
	   "    if not ret and ret != None:\n"
	   "        return ret\n"
	   "return True\n") +"\n" +
    indent(4,"\n    def adapter_exit(verdict,reason):\n") + "\n" +
    indent(8,"for x in "+class_name()+".adapter_exit_list:\n"
	   "    ret = x(verdict,reason)\n"
	   "    if not ret and ret != None:\n"
	   "        return ret\n"
	   "return True\n")+ "\n" ;

  return s + "\nModel = _gen_" + *name + "\n";
}
