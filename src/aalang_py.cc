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
                          std::string& funcname,int i)
{
  funcname = "action" + acnt + s;
  return "    def " + funcname + "():\n" + variables
    +    "        action_name = \"" + multiname[i] + "\"\n"
    +    "        action_index = " + to_string(i) + "\n"
    +    indent(8,cfl.first)+"\n";
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


void aalang_py::set_name(std::string* name)
{
  multiname.push_back(*name);
}

void aalang_py::set_namestr(std::string* _name)
{
  name=_name;
  s+="import aalmodel\n"
    "class _gen_"+*name+"(aalmodel.AALModel):\n"
    "    def __init__(self):\n"
    "        aalmodel.AALModel.__init__(self, globals())\n";
}

void aalang_py::set_variables(std::string* var,const char* file,int line,int col)
{
  variables="        global " + indent(0,*var) + "\n";
  m_lines_in_vars = std::count(variables.begin(), variables.end(), '\n');
  delete var;
}

void aalang_py::set_istate(std::string* ist,const char* file,int line,int col)
{
  const std::string funcname("initial_state");
  s += "\n    def " + funcname + "():\n" + variables +
    indent(8, *ist) + "\n";
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

void aalang_py::set_tagname(std::string* name)
{
  multiname.push_back(*name);
  delete name;
  tag = true;
  adapter = false;
}

void aalang_py::next_tag()
{
  for (unsigned int i = 0; i < multiname.size(); i++) {
    s+="\n    tag" + to_string(tag_cnt) + "name = \""+multiname[i]+"\"\n";
    /* tagXguard */
    const std::string funcname("tag" + to_string(tag_cnt) + "guard");
    s+="    def " + funcname + "():\n" + variables;
    s+="        tag_name = \"" + multiname[i] + "\"\n";
    s+=indent(8,m_guard.first)+"\n";

    s+=python_lineno_wrapper(m_guard,funcname,2+m_lines_in_vars,4,
                             ", \"guard of tag \\\"" + multiname[i]
                             + "\\\"\")");

    if (adapter) {
      const std::string funcname("tag" + to_string(tag_cnt) + "adapter");

      s+="    def " + funcname + "():\n" + variables;
      s+="        tag_name = \"" + multiname[i] + "\"\n";
      s+=indent(8,m_adapter.first)+"\n";

      s+=python_lineno_wrapper(m_adapter,funcname,2+m_lines_in_vars,4,
			       ", \"adapter of tag \\\"" + multiname[i]
			       + "\\\"\")");
    }

    tag_cnt++;
  }
  multiname.clear();
  tag = false;
  adapter = false;
}

void aalang_py::set_guard(std::string* gua,const char* file,int line,int col)
{
  default_if_empty(*gua, "return True");
  m_guard = codefileline(*gua,fileline(file,line));
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
  for (unsigned int i = 0; i < multiname.size(); i++) {
    std::string funcname;
    /* actionXname, actionXtype */
    s+="\n    action" + acnt + "name = \"" + multiname[i] + "\"\n"
      +"    action" + acnt + "type = ";
    if (multiname[i].size() > 0 && multiname[i].c_str()[0] == 'o') {
      s += "\"output\"\n";
      this_is_input = false;
    } else {
      s += "\"input\"\n";
      this_is_input = true;
    }

    /* actionXguard */

    s+=action_helper(m_guard,"guard",funcname,i);
    s+=python_lineno_wrapper(m_guard,funcname,3+m_lines_in_vars,4,
                             ", \"guard of action \\\"" + multiname[i] +
                             "\\\"\")");

    /* actionXbody */
    s+=action_helper(m_body,"body",funcname,i);
    s+=python_lineno_wrapper(m_body,funcname,3+m_lines_in_vars,4,
                             ", \"body of action \\\"" + multiname[i] +
                             "\\\"\")");
    /* actionXadapter */
    s+=action_helper(m_adapter,"adapter",funcname,i);
    if (this_is_input) {
      s+="        return " +acnt + "\n";
    } else {
      s+="        return False\n";
    }
    s+=python_lineno_wrapper(m_adapter,funcname,3+m_lines_in_vars,4,
                             ", \"adapter of action \\\"" + multiname[i]
                             + "\\\"\")");

    action_cnt++;
    acnt=to_string(action_cnt);
  }
  multiname.clear();
}

std::string aalang_py::stringify()
{
  return s + "\nModel = _gen_" + *name + "\n";
}
