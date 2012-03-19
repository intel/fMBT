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

void aalang_py::set_starter(std::string* st)
{
  s+=indent(0, *st)+"\n";
}


void aalang_py::set_name(std::string* name)
{
  s+="\n    action"+acnt+"name = \""+*name+"\"\n"
    +"    action"+acnt+"type = \"input\"\n";
}

void aalang_py::set_namestr(std::string* _name)
{ 
  name=_name;
  s+="import aalmodel\n"
    "class _gen_"+*name+"(aalmodel.AALModel):\n"
    "    def __init__(self):\n"
    "        aalmodel.AALModel.__init__(self, globals())\n";
}

void aalang_py::set_variables(std::string* var)
{
  variables="        global " + indent(0,*var) + "\n";
  delete var;
}

void aalang_py::set_istate(std::string* ist)
{
  s += "\n    def initial_state():\n" + variables +
    indent(8, *ist) + "\n";
}

void aalang_py::set_tagname(std::string* name)
{
  s+="\n    tag" + to_string(tag_cnt) + "name = \""+*name+"\"\n";
  delete name;
  tag = true;
}

void aalang_py::next_tag()
{
  tag_cnt++;
  tag = false;
}

void aalang_py::set_guard(std::string* gua)
{
  default_if_empty(*gua, "return True");
  if (tag) {
    s+="    def tag"+to_string(tag_cnt)+"guard():\n"+ variables +
      indent(8,*gua)+"\n";
  }
  else {
    s+="    def action"+acnt+"guard():\n"+variables + 
      "        try:\n" +
      indent(12,*gua) + "\n" +
      "        except Exception as _aalException:\n" +
      "            raise _aalException\n";
  }
}

void aalang_py::set_push(std::string* p)
{
  push=*p;
  delete p;
}

void aalang_py::set_pop(std::string* p)
{
  pop=*p;
  delete p;
}

void aalang_py::set_body(std::string* bod)
{
  default_if_empty(*bod, "pass");
  s+="    def action"+acnt+"body():\n" + variables +
    "        try:\n" +
                 indent(12,*bod)+"\n"
    "        except Exception as _aalException:\n"
    "            raise _aalException\n";
}

void aalang_py::set_adapter(std::string* ada)
{
  default_if_empty(*ada, "pass");
  s+="    def action"+acnt+"adapter():\n" + variables +
              indent(8,*ada)+"\n"+
     "        return " +acnt + "\n";
}

void aalang_py::next_action()
{
  action_cnt++;
  acnt=to_string(action_cnt);
}

std::string aalang_py::stringify()
{
  return s + "\nModel = _gen_" + *name + "\n";
}
