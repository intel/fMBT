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

  /*
  std::list<std::string>::iterator i=l.begin();
  if (i==l.end()) {
    return ret;
  }
  i++;
  for(;i!=l.end();i++) {
    ret=ret + " , " + "\"" + *i + "(\"";
  }
  */
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
  return "    def " + funcname + "():\n" + variables
    +    "        action_name = \"" + multiname[i].first + "\"\n"
    +    "        action_index = " + to_string(i) + "\n"
    +    indent(8,cfl.first)+"\n";
}

const std::string aalang_py::class_name() const
{
  return "_gen_" + *name;
}

const std::string aalang_py::serial_guard(bool cls) const
{
  std::string guard_name = "serial" + to_string(serial_stack.back()) + "guard";
  if (cls) return class_name() + "." + guard_name;
  else return guard_name;
}

const std::string aalang_py::serial_step(bool cls) const
{
  std::string step_name = "serial" + to_string(serial_stack.back()) + "step";
  if (cls) return class_name() + "." + step_name;
  else return step_name;
}

void default_if_empty(std::string& s, const std::string& default_value)
{
  size_t first_nonspace = s.find_first_not_of(" \t\n\r");
  if (first_nonspace == std::string::npos) s = default_value;
}

void aalang_py::set_starter(std::string* st,const char* file,int line,int col)
{
  s+=indent(0, *st)+"\n";
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
  }

  multiname.push_back(std::pair<std::string,int>(*name,action_cnt));
  action_cnt++;

  if (first) {
    guard_requires.push_back("action"+to_string(action_cnt-1)+"guard");
  }

}

void aalang_py::set_namestr(std::string* _name)
{
  name=_name;
  s+="import aalmodel\n"
    "class " + class_name() + "(aalmodel.AALModel):\n"
    "    def __init__(self):\n"
    "        aalmodel.AALModel.__init__(self, globals())\n";
}

void aalang_py::set_variables(std::string* var,const char* file,int line,int col)
{
  std::string ivar = indent(0,*var);
  if (ivar!="") {
    variables="        global " + indent(0,*var) + "\n";
  }
  m_lines_in_vars = std::count(variables.begin(), variables.end(), '\n');
  delete var;
}

void aalang_py::set_istate(std::string* ist,const char* file,int line,int col)
{
  const std::string funcname("initial_state");
  s += "\n    def " + funcname + "():\n" + variables +
    indent(8, *ist) + "\n" +
    indent(8, "pass") + "\n";
  s += python_lineno_wrapper(file,line,funcname,1+m_lines_in_vars,4);
}

void aalang_py::set_ainit(std::string* iai,const char* file,int line,int col)
{
  const std::string r("return 1");
  const std::string funcname("adapter_init");
  s += "\n    def " + funcname + "():\n" + variables +
    indent(8, *iai) + "\n" + indent(8, r) + "\n";
  s += python_lineno_wrapper(file,line,funcname,1+m_lines_in_vars,4);
}

void aalang_py::set_aexit(std::string* iai,const char* file,int line,int col)
{
  const std::string funcname("adapter_exit");
  s += "\n    def " + funcname + "(verdict,reason):\n" + variables +
    indent(8, *iai) + "\n" "\n";
  s += python_lineno_wrapper(file,line,funcname,1+m_lines_in_vars,4);
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
  default_if_empty(*gua, "return True");
  m_guard = codefileline(*gua,fileline(file,line));
}

void aalang_py::parallel(bool start) {

}

void aalang_py::serial(bool start) {
    if (start) {
      serial_stack.push_back(serial_cnt);
      s += "\n"
        "    def " + serial_guard() + "():\n"
        "        return " + serial_guard(true) + "_active_block == guard_list[-2]\n"
        "    " + serial_guard() + ".blocks = []\n"
        "    def " + serial_step() + "():\n"
        "        " + serial_guard(true) + "_active_block_num = (" +
        serial_guard(true) + "_active_block_num + 1) % " + serial_guard(true) +
        "_block_count\n" +
        "        " + serial_guard(true) + "_active_block = " + serial_guard(true) +
        ".blocks[" + serial_guard(true) + "_active_block_num]\n";
      serial_cnt += 1;
    } else {
      s += "\n"
        "    " + serial_guard() + "_block_count = len(" + serial_guard() + ".blocks)\n"
        "    if " + serial_guard() + "_block_count > 0:\n"
        "        " + serial_guard() + "_active_block_num = 0\n"
        "        " + serial_guard() + "_active_block = " + serial_guard() + ".blocks[0]\n";
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
  default_if_empty(*bod, "pass");
  m_body = codefileline(*bod,fileline(file,line));
}

void aalang_py::set_adapter(std::string* ada,const char* file,int line,int col)
{
  adapter = true;
  default_if_empty(*ada, "pass");
  m_adapter = codefileline(*ada,fileline(file,line));
}

void aalang_py::next_action()
{
  std::string acnt;
  guard_requires.pop_back();
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

    if (!serial_stack.empty()) {
      s += "    " + serial_guard(false) + ".blocks.append(\"" + multiname[i].first + "\")\n";
    }
    /* actionXguard */

    s+=action_helper(m_guard,"guard",funcname,i,acnt);

    // action + acnt + guard.requires=[...];
    s+="    action" + acnt + "guard.requires = [" + requires + "]\n";
    if (!serial_stack.empty()) {
      s+="    action" + acnt + "guard.requires += [\"" + serial_guard(false) + "\"]\n";
    }

    s+=python_lineno_wrapper(m_guard,funcname,3+m_lines_in_vars,4,
                             ", \"guard of action \\\"" + multiname[i].first +
                             "\\\"\")");

    /* actionXbody */
    s+=action_helper(m_body,"body",funcname,i,acnt);
    s+=python_lineno_wrapper(m_body,funcname,3+m_lines_in_vars,4,
                             ", \"body of action \\\"" + multiname[i].first +
                             "\\\"\")");
    if (!serial_stack.empty()) {
      s += "    action" + acnt + "body.postcall = ["
        + serial_step(false) + "]\n";
    }
    /* actionXadapter */
    s+=action_helper(m_adapter,"adapter",funcname,i,acnt);
    if (this_is_input) {
      s+="        return " +acnt + "\n";
    } else {
      s+="        return False\n";
    }
    s+=python_lineno_wrapper(m_adapter,funcname,3+m_lines_in_vars,4,
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
  return s + "\nModel = _gen_" + *name + "\n";
}
