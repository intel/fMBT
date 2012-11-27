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

std::string indent(int depth, std::string &s)
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
        rv += s.substr(line_start + offset - depth, line_end - line_start - offset + depth + 1);
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
  delete var;
}

void aalang_py::set_istate(std::string* ist,const char* file,int line,int col)
{
  s += "\n    def initial_state():\n" + variables +
    indent(8, *ist) + "\n";
}

void aalang_py::set_ainit(std::string* iai,const char* file,int line,int col)
{
  std::string r("return 1");
  s += "\n    def adapter_init(self):\n" + variables +
    indent(8, *iai) + "\n" + indent(8, r) + "\n";
}


void aalang_py::set_tagname(std::string* name)
{
  s+="\n    tag" + to_string(tag_cnt) + "name = \""+*name+"\"\n";
  multiname.push_back(*name);
  delete name;
  tag = true;
}

void aalang_py::next_tag()
{
  tag_cnt++;
  multiname.clear();
  tag = false;
}

void aalang_py::set_guard(std::string* gua,const char* file,int line,int col)
{
  default_if_empty(*gua, "return True");
  if (tag) {
    s+="    def tag"+to_string(tag_cnt)+"guard():\n"+ variables;
    if (gua->find("tag_name") != std::string::npos)
      s+="        tag_name = '" + multiname[0] + "'\n";
    s+=indent(8,*gua)+"\n";
  }
  else {
    m_guard = *gua;
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
  m_body = *bod;
}

void aalang_py::set_adapter(std::string* ada,const char* file,int line,int col)
{
  default_if_empty(*ada, "pass");
  m_adapter = *ada;
}

void aalang_py::next_action()
{
  for (unsigned int i = 0; i < multiname.size(); i++) {
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
    s+="    def action" + acnt + "guard():\n" + variables;
    if (m_guard.find("action_name") != std::string::npos)
      s+="        action_name = \"" + multiname[i] + "\"\n";
    if (m_guard.find("action_index") != std::string::npos)
      s+="        action_index = " + to_string(i) + "\n";
    s+="        try:\n" +
      indent(12,m_guard) + "\n" +
      "        except Exception as _aalException:\n" +
      "            raise _aalException\n";

    /* actionXbody */
    s+="    def action"+acnt+"body():\n" + variables;
    if (m_body.find("action_name") != std::string::npos)
      s+="        action_name = \"" + multiname[i] + "\"\n";
    if (m_body.find("action_index") != std::string::npos)
      s+="        action_index = " + to_string(i) + "\n";
    s+="        try:\n" +
      indent(12,m_body)+"\n"
      "        except Exception as _aalException:\n"
      "            raise _aalException\n";

    /* actionXadapter */
    s+="    def action"+acnt+"adapter():\n" + variables;
    if (m_adapter.find("action_name") != std::string::npos)
      s+="        action_name = \"" + multiname[i] + "\"\n";
    if (m_adapter.find("action_index") != std::string::npos)
      s+="        action_index = " + to_string(i) + "\n";
    s+=indent(8,m_adapter)+"\n";
    if (this_is_input) {
      s+="        return " +acnt + "\n";
    } else {
      s+="        return False\n";
    }

    action_cnt++;
    acnt=to_string(action_cnt);
  }
  multiname.clear();
}

std::string aalang_py::stringify()
{
  return s + "\nModel = _gen_" + *name + "\n";
}
