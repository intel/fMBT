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

#include "aalang_cpp.hh"
#include "helper.hh"

aalang_cpp::aalang_cpp(): aalang(),action_cnt(1), tag_cnt(1), name_cnt(0),
			  istate(NULL), name(NULL), tag(false)
{
  default_guard="return true;"; 
  default_body="";
  default_adapter="";
  std::vector<std::string> t;
  aname.push_back(t);
  tname.push_back(t);
  amap.push_back(0);
  tmap.push_back(0);
  anames.push_back(default_body);
}

aalang_cpp::~aalang_cpp()
{
  if (istate)
    delete istate;
  if (name)
    delete name;
}


void aalang_cpp::set_starter(std::string* st)
{
  s+=*st;
  delete st;
}

void aalang_cpp::set_name(std::string* name)
{
  s+="\n//action"+to_string(action_cnt)+": \""+*name+"\"\n";
  anames.push_back(*name);
  aname.back().push_back(*name);
  delete name;
  amap.push_back(action_cnt);
  name_cnt++;
}

void aalang_cpp::set_namestr(std::string* _name)
{ 
  name=_name;
  s+="#include \"aal.hh\"\n\n";
  s+="class _gen_"+*name+":public aal {\nprivate:\n\t";
}

void aalang_cpp::set_variables(std::string* var)
{
  s+="//variables\n"+*var+"\n";
  delete var;
}

void aalang_cpp::set_istate(std::string* ist)
{
  istate=ist;
}

void aalang_cpp::set_push(std::string* p)
{
  push=*p;
  delete p;
}

void aalang_cpp::set_pop(std::string* p)
{
  pop=*p;
  delete p;
}

void aalang_cpp::set_tagname(std::string* name)
{
  s+="\n//tag"+to_string(tag_cnt)+": \""+*name+"\"\n";
  tname.back().push_back(*name);
  delete name;
  tmap.push_back(tag_cnt);
  name_cnt++;
  tag=true;
}

void aalang_cpp::next_tag()
{
  std::vector<std::string> t;
  tname.push_back(t);
  tag_cnt+=name_cnt;
  name_cnt=0;
  tag=false;
}

void aalang_cpp::set_guard(std::string* gua)
{
  if (tag) {
    s+="bool tag"+to_string(tag_cnt)+"_guard() {\n"+
      *gua+"}\n";
  } else {
    s+="bool action"+to_string(action_cnt)+"_guard() {\n"+
      *gua+"}\n";
  }
  if (gua!=&default_guard) 
    delete gua;
}

void aalang_cpp::set_body(std::string* bod)
{
  s+="void action"+to_string(action_cnt)+"_body() {\n"+*bod+"}\n";
  if (bod!=&default_body) 
    delete bod;
}

void aalang_cpp::set_adapter(std::string* ada)
{
  s+="int action" + to_string(action_cnt) + "_adapter(const char* param) {\n" +
      *ada + "\n"
      "\treturn " + to_string(action_cnt) + ";\n"
      "}\n";
  if (ada!=&default_adapter)
      delete ada;
}

void aalang_cpp::next_action()
{
  std::vector<std::string> t;
  aname.push_back(t);
  action_cnt+=name_cnt;
  name_cnt=0;
}

std::string aalang_cpp::stringify()
{

  s=s+
    "\npublic:\n"
    "\t_gen_"+*name+"(Log& l, std::string& params): aal(l, params) {\n\taction_names.push_back(\"\");\n";

  for(std::list<std::vector<std::string> >::iterator i=aname.begin();i!=aname.end();i++) {
    for(std::vector<std::string>::iterator j=i->begin();j!=i->end();j++) {
      s+="\taction_names.push_back(\""+*j+"\");\n";
    }
  }
  s=s+"\ttag_names.push_back(\"\");\n";

  for(std::list<std::vector<std::string> >::iterator i=tname.begin();i!=tname.end();i++) {
    for(std::vector<std::string>::iterator j=i->begin();j!=i->end();j++) {
      s+="\ttag_names.push_back(\""+*j+"\");\n";
    }
  }

  if (!istate) {
    istate=new std::string("//default istate\n");
  }

  s+=*istate+"}\n"
    "virtual bool reset() {\n"+
    *istate +
    "return true;\n}\n\n";

  if (pop!="") {
    s=s+"\nvirtual void pop(){\n"+pop+"\n}\n";
    s=s+"\nvirtual void push(){\n"+push+"\n}\n";
  }

  s=s+"virtual int observe(std::vector<int>&action, bool block){\n"
    "\taction.clear();\n"
    "\tdo {\n"
    "\tint r;\n";

  int obsa=0;

  for(int i=1;i<action_cnt;i++) {
    if (anames[i][0]=='o') {
      obsa++;
      s=s+"\tr=action"+to_string(amap[i])+"_adapter(NULL);\n"
	"\tif (r) { action.push_back(r); return 1;}\n";
    }
  }
  if (!obsa) {
    s=s+"\treturn SILENCE;\n";
  }
  s=s+"\t} while(block);"
    "\treturn 0;\n"
    "}\n";
  
  s=s+"virtual int adapter_execute(int action,const char* param) {\n"
    "\tswitch(action) {\n";
  
  for(int i=1;i<action_cnt;i++) {
    if (anames[i][0]=='i') {
      s+="\t\tcase "+to_string(i)+":\n"
	"\t\treturn action"+to_string(amap[i])+
	"_adapter(param);\n\t\tbreak;\n";
    }
  }
  s=s+"\t\tdefault:\n"
    "\t\treturn 0;\n"
    "\t};\n"
    "}\n"
    "virtual int model_execute(int action) {\n"
    "\tswitch(action) {\n";

  for(int i=1;i<action_cnt;i++) {
    s+="\t\tcase "+to_string(i)+":\n"
      "\t\taction"+to_string(amap[i])+"_body();\n\t\treturn "+
      to_string(i)+";\n\t\tbreak;\n";
  }
  s=s+"\t\tdefault:\n"
    "\t\treturn 0;\n"
    "\t};\n"
    "}\n"
    "virtual int getActions(int** act) {\n"
    "actions.clear();\n";
  
  for(int i=1;i<action_cnt;i++) {
    s+="\tif (action"+to_string(amap[i])+"_guard()) {\n"
      "\t\tactions.push_back("+to_string(i)+");\n"
      "\t}\n";
  }
  s=s+"\t*act = &actions[0];\n"
    "\treturn actions.size();\n"
    "}\n";
  
  s=s+"virtual int getprops(int** props) {\n"
    "tags.clear();\n";

  for(int i=1;i<tag_cnt;i++) {
    s+="\tif (tag"+to_string(tmap[i])+"_guard()) {\n"
      "\t\ttags.push_back("+to_string(i)+");\n"
      "\t}\n";
  }
  s=s+"\t*props = &tags[0];\n"
    "\treturn tags.size();\n"
    "}\n"
    "};\n";

  factory_register();
  
  return s;
}

void aalang_cpp::factory_register()
{
  s=s+"  /* factory register */\n\n"
    "namespace {\n"
    "static aal* a=NULL;\n\n"
    "void _atexitfunc()\n"
    "  {\n"
    "    if (a) {\n"
    "      delete a;\n"
    "      a=NULL;\n"
    "    }\n"
    "  }\n"
    "Model* model_creator(Log&l, std::string params) {\n"
    "\tif (!a) {\n"
    "\t  a=new _gen_"+*name+"(l, params);\n"
    "\t  atexit(_atexitfunc);\n"
    "\t}\n"
    "\treturn new Mwrapper(l,params,a);\n"
    "}\n\n"
    "static ModelFactory::Register me1(\""+*name+"\", model_creator);\n\n"
    "Adapter* adapter_creator(Log&l, std::string params = \"\")\n"
    "{\n"
    "\tif (!a) {\n"
    "\t  a=new _gen_"+*name+"(l, params);\n"
    "\t  atexit(_atexitfunc);\n"
    "\t}\n"
    "\treturn new Awrapper(l,params,a);\n"
    "}\n"
    "static AdapterFactory::Register me2(\""+*name+"\", adapter_creator);\n"+
    "}\n";
}
