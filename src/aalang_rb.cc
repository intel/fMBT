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

#include "aalang_rb.hh"
#include "aalang_py.hh"
#include "helper.hh"
#include <algorithm>

std::string aalang_rb::action_helper(const codefileline& cfl,std::string s,
				     std::string& funcname,int i,std::string& acnt)
{
  funcname = "action" + acnt + s;
  std::string extra_name;
  if (action_name_type == aalang::IACT)
      extra_name = "input_name =\"" + multiname[i].first.substr(2) + "\"";
  else if (action_name_type == aalang::OBSERVE)
      extra_name = "output_name =\"" + multiname[i].first.substr(2)  + "\"";


  return "    def " + funcname + "()\n" 
    +    "        action_name = \"" + multiname[i].first + "\"\n"
    +    "        " + extra_name + "\n"
    +    "        action_index = " + to_string(i) + "\n"
    +    indent(8,cfl.first)+"\n";
}

const std::string aalang_rb::class_name() const
{
  return "Gen_" + *name;
}

const std::string aalang_rb::serialN(const std::string postfix, bool cls) const
{
  // returns [cls.]serial(currentblock)<postfix>
  std::string full_name = "serial" + to_string(abs(serial_stack.back())) + postfix;
  if (cls) return class_name() + "." + full_name;
  else return full_name;
}

const std::string aalang_rb::serialN_1(const std::string postfix, bool cls) const
{
  // returns [cls.]serial(outerblock "N-1")<postfix>
  std::list<int>::const_iterator outer_serial = serial_stack.end();
  --outer_serial; --outer_serial;
  std::string full_name = "serial" + to_string(abs(*outer_serial)) + postfix;
  if (cls) return class_name() + "." + full_name;
  else return full_name;
}

const int aalang_rb::serial_stackN_1() const
{
  std::list<int>::const_iterator outer_serial = serial_stack.end();
  --outer_serial; --outer_serial;
  return *outer_serial;
}

void aalang_rb::set_starter(std::string* st,const char* file,int line,int col)
{
  s+=indent(0, *st)+"\n";
  delete st;
}


void aalang_rb::set_name(std::string* name,bool first,ANAMETYPE t)
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

aalang_rb::~aalang_rb()
{
  if (name)
    delete name;
}

void aalang_rb::set_namestr(std::string* _name)
{
  name=_name;
  s+="require 'rubygems'\n" +
    "require 'fmbt-ruby'\n" +
    "require 'aalmodel'\n" +
    "require 'set'\n" +
    "class " + class_name() + "< AALModel\n"
    "    def initialize()\n";
  s+="        @adapter_init_list = []\n";
  s+="        @initial_state_list = []\n";
  s+="        @adapter_exit_list = []\n";
  s+="        @push_variables_set = Set.new()\n";
  s+="        super()\n";
  s+="    end\n";
}

void aalang_rb::set_variables(std::string* var,const char* file,int line,int col)
{
  //get instance variables name
  std::string delimiter = ",";
  size_t last = 0; 
  size_t next = 0; 
  std::string ruby_global_variables = "";
  std::string variables_temp = *var;
  variables_temp.erase(std::remove(variables_temp.begin(), variables_temp.end(), ' '), variables_temp.end());
  variables_temp.erase(std::remove(variables_temp.begin(), variables_temp.end(), '@'), variables_temp.end());
  while ((next = variables_temp.find(delimiter, last)) != std::string::npos) 
  { 
      variables += variables_temp.substr(last, next-last) + "=nil \n"; 
      last = next + 1;
  }
  variables += variables_temp.substr(last, next-last) + "= nil \n";
  delete var;
}

void aalang_rb::set_istate(std::string* ist,const char* file,int line,int col)
{
  model_init_counter++;
  
  const std::string funcname("initial_state"+to_string(model_init_counter));
  s += "\n    def " + funcname + "()\n"  +
    indent(8, *ist) + "\n" +
    indent(8, variables) + "\n" +
    indent(8, "user_definedd_variable = local_variables") + "\n" +
    indent(8, "user_definedd_variable.pop()") + "\n" +   
    indent(8, "user_definedd_variable.each do |item|") + "\n" +
    indent(12, "@push_variables_set.add(item)") + "\n" +
    indent(12, "@variables[item] = \"#{item.to_s}\"") + "\n" +
    indent(8, "end") + "\n" + 
    indent(4, "end") + "\n";
  instance_variables += "        @initial_state_list.push('"+funcname+"')"+"\n";
  delete ist;
}

void aalang_rb::set_ainit(std::string* iai,const char* file,int line,int col)
{
  adapter_init_counter++;
  const std::string r("return 1");
  const std::string funcname("adapter_init"+to_string(adapter_init_counter));
  s += "\n    def " + funcname + "()\n"  +
    indent(8, *iai) + "\n" + indent(8, r) + "\n" + indent(4, "end") + "\n";

  instance_variables += "        @adapter_init_list.push('"+funcname+"')"+"\n";
  delete iai;
}

void aalang_rb::set_aexit(std::string* iai,const char* file,int line,int col)
{
  adapter_exit_counter++;
  const std::string funcname("adapter_exit"+to_string(adapter_exit_counter));
  s += "\n    def " + funcname + "(verdict,reason)\n"  +
    indent(8, *iai) + "\n" + "\n"+indent(4, "end")+"\n";


  instance_variables += "        @adapter_exit_list.push('"+funcname+"')"+"\n";
  delete iai;
}

void aalang_rb::set_tagname(std::string* name,bool first)
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

void aalang_rb::next_tag()
{
  std::string tcnt;
  guard_requires.pop_back();

  requires = to_list(guard_requires);

  for (unsigned int i = 0; i < multiname.size(); i++) {
    tcnt=to_string(multiname[i].second);

    tag_names+="\n        @tag" + tcnt + "name = \""+multiname[i].first+"\"";
    /* tagXguard */
    const std::string funcname("tag" + tcnt + "guard");
    s+="    def " + funcname + "()\n" ;
    s+="        tag_name = \"" + multiname[i].first + "\"\n";
    s+=indent(8,m_guard.first)+"\n";
    s+="    end\n";

    if (adapter) {
      const std::string funcname("tag" + tcnt + "adapter");

      s+="    def " + funcname + "()\n" ;
      s+="        tag_name = \"" + multiname[i].first + "\"\n";
      s+=indent(8,m_adapter.first)+"\n";
      s+="    end\n";
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

void aalang_rb::set_guard(std::string* gua,const char* file,int line,int col)
{
  std::string tmp=*gua;
  if (gua!=&default_guard)
    delete gua;
  default_if_empty(tmp, "return true");
  m_guard = codefileline(tmp,fileline(file,line));
}

void aalang_rb::parallel(bool start,std::list<std::string>* __params) {
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
      "    def " + serialN("guard") + "()\n"
      "        return guard_list[-2] in " + serialN("guard", true) +
      "_next_block\n"
      "    " + serialN("guard") + ".requires = []\n"
      "    " + serialN("guard") + ".blocks = []\n"
      "    " + serialN("guard") + "_next_block = set()\n"
      "    def " + serialN("step") + "(self, upper)\n"
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
        serialN("guard", true) + ".blocks)\n"
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

void aalang_rb::serial(bool start,std::list<std::string>* __params) {

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
      "    def " + serialN("guard") + "()\n"
      "        return " + serialN("guard", true) +
      "_next_block[-1] == guard_list[-2]\n"
      "    " + serialN("guard") + ".requires = []\n"
      "    " + serialN("guard") + ".blocks = []\n"
      "    " + serialN("guard") + "_next_block = []\n"
      "    def " + serialN("step") + "(self, upper)\n"
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

void aalang_rb::set_push(std::string* p,const char* file,int line,int col)
{
  push=*p;
  delete p;
}

void aalang_rb::set_pop(std::string* p,const char* file,int line,int col)
{
  pop=*p;
  delete p;
}

void aalang_rb::set_body(std::string* bod,const char* file,int line,int col)
{
  std::string tmp=*bod;
  if (bod!=&default_body)
    delete bod;
  default_if_empty(tmp, "");
  m_body = codefileline(tmp,fileline(file,line));
}

void aalang_rb::set_adapter(std::string* ada,const char* file,int line,int col)
{
  adapter = true;
  std::string tmp=*ada;
  if (ada!=&default_adapter)
    delete ada;
  default_if_empty(tmp, "");
  m_adapter = codefileline(tmp,fileline(file,line));
}

void aalang_rb::next_action()
{
  std::string acnt;
  guard_requires.pop_back();
  serial_stack.pop_back();
  requires = to_list(guard_requires);

  for (unsigned int i = 0; i < multiname.size(); i++) {
    std::string funcname;
    acnt = to_string(multiname[i].second);
    
    /* actionXname, actionXtype */
    action_names_types+="\n        @action" + acnt + "name = \"" + multiname[i].first + "\"\n"
      +"        @action" + acnt + "type = ";
    if (multiname[i].first.size() > 0 && multiname[i].first.c_str()[0] == 'o') {
      action_names_types += "\"output\"";
      this_is_input = false;
    } else {
      action_names_types += "\"input\"";
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
    s+="    end\n";
    if (!serial_stack.empty() && serial_stack.back() != 0) {
      s+="    action" + acnt + "guard.requires += [\"" + serialN("guard") + "\"]\n";
    }


    /* actionXbody */
    s+=action_helper(m_body,"body",funcname,i,acnt);
    s+="    end\n";

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
    s+="    end\n";

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

std::string aalang_rb::stringify()
{
  //ruby need to initialize instance variables in initialize()
  size_t pos = s.find("super()", 0);
  s.insert(pos-8,"\n"+instance_variables);
  pos = s.find("@initial_state_list", 0);
  s.insert(pos-8,"\n"+action_names_types+"\n");
  pos = s.find("@initial_state_list", 0);
  s.insert(pos-8,"\n"+tag_names+"\n");
      
  s += indent(4,"\n    def adapter_init()\n") + "\n" +
    indent(8,"for x in @adapter_init_list\n"
	   "    ret = self.send(x)\n"
	   "    if not ret and ret != nil\n"
	   "        return ret\n"
     "    end\n")+"\n"+
	indent(8,"\n    end") + "\n" +
    indent(8,"      return true\n") + "\n" +
    indent(4,"\n    end") + "\n" +
    indent(4,"\n    def initial_state()\n") + "\n" +
    indent(8,"for x in @initial_state_list\n"
	   "    ret = self.send(x)\n"
	   "    if not ret and ret != nil\n"
     "        return ret\n"
	   "    end\n")+"\n"+
	indent(8,"\n    end") + "\n" +
    indent(8,"      return true\n") + "\n" +
    indent(4,"\n    end") + "\n" + 
    indent(4,"\n    def adapter_exit(verdict,reason)\n") + "\n" +
    indent(8,"for x in @adapter_exit_list\n"
	   "    ret = self.send(x,verdict,reason)\n"
	   "    if not ret and ret != nil\n"
	   "        return ret\n"
     "    end\n") + "\n" +
    indent(8,"\n    end") + "\n" +
    indent(8,"      return true\n") + "\n" +
    indent(4,"\n    end") + "\n" +
    "\nend"+
    "\nclass Model < "+ class_name() + "\n" +
    indent(4,"def initialize()") + "\n" +
    indent(8,"super()") + "\n" +
    indent(4,"end") + "\n" + 
    "end";

  return s;
}
