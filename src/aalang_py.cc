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

std::string lstrip(const std::string &s)
{
  return s.substr(s.find_first_not_of(" \t"));
}

std::string indent(int depth, std::string &s)
{
  std::string rv;
  std::string row = lstrip(s);
  for (int i=0; i<depth; i++) rv+=" ";
  // TODO: do this properly.
  // calculate white space offset on the first non-empty line
  // apply the same offset to every line on the block.
  rv += row;
  return rv;
}

void aalang_py::set_starter(std::string* st)
{
  s+=*st+"\n";
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
    "class _gen_"+*name+"(aalmodel.AALModel):\n";
}

void aalang_py::set_variables(std::string* var)
{
  variables="        global " + *var + "\n";
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
  s+="    def action"+acnt+"body():\n" + variables +
    "        try:\n" +
    indent(12,*bod)+"\n"
    "        except Exception as _aalException:\n"
    "            raise _aalException\n";
}

void aalang_py::set_adapter(std::string* ada)
{
  s+="    def action"+acnt+"adapter():\n" + variables +
    "        try:\n" +
    indent(12,*ada)+"\n"+
    "        except Exception as _aalException:\n"
    "            return 0 # i should log the exception...\n"
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
