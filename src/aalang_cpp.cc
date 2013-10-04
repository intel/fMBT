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

std::string to_call(std::list<std::string>& l) {
  if (l.begin()==l.end()) {
    return "";
  }

  std::string ret="(" + l.front();

  std::list<std::string>::iterator i=l.begin();
  if (i==l.end()) {
    return ret;
  } 
 i++;
  for(;i!=l.end();i++) {
    ret=ret + " && " + *i;
  }
  ret = ret + ")";
  return ret;
}

aalang_cpp::aalang_cpp(): aalang(),action_cnt(1), tag_cnt(1), name_cnt(0),
			  istate(NULL),ainit(NULL), aexit(NULL), name(NULL),
			  tag(false),outters(0),current_outter(-1),current_inner(0)
{
  default_guard="return true;//default"; 
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
  if (ainit)
    delete ainit;
  if (aexit)
    delete aexit;
  if (name)
    delete name;
}

std::string to_line(const char* f,int line)
{
  if (line) {
    return "\n#line "+to_string(line)+" \""+f+"\"\n";
  }
  return "";
}

void aalang_cpp::set_starter(std::string* st,const char* file,int line,int col)
{
  s+=to_line(file,line)+*st;
  delete st;
}

void aalang_cpp::set_name(std::string* name,bool first,ANAMETYPE t)
{
  current_inner++;
  if (current_outter>0) {
    inner_names[current_outter-1].push_back(*name);
  }
  if (first) {
    tstack.push_back(tag);
    tag=false;
    name_cnt_stack.push_back(action_cnt);
    name_cnt_stack.push_back(name_cnt);
    name_cnt=0;
    action_cnt=anames.size();
  }

  if (name_cnt==0) {
    guard_call_construct.push_back("action"+to_string(action_cnt)+"_guard(action_names["+to_string(action_cnt) +"])");
    action_guard_call.push_back(to_call(guard_call_construct));
  } else {
    std::string tmp=guard_call_construct.back();
    guard_call_construct.pop_back();
    guard_call_construct.push_back("action"+to_string(action_cnt)+"_guard(action_names["+to_string(action_cnt+name_cnt) +"])");    
    action_guard_call.push_back(to_call(guard_call_construct));
    guard_call_construct.pop_back();
    guard_call_construct.push_back(tmp);
 }

  anames.push_back(*name);
  aname.back().push_back(*name);
  amap.push_back(action_cnt);
  s+="\n//action"+to_string((int)anames.size()-1)+": \""+*name+"\"\n";
  name_cnt++;
  delete name;
}

void aalang_cpp::set_namestr(std::string* _name)
{ 
  name=_name;
  s+="#include \"aal.hh\"\n\n";
  s+="class _gen_"+*name+":public aal {\nprivate:\n\t";
}

void aalang_cpp::set_variables(std::string* var,const char* file,int line,int col)
{
  s+=to_line(file,line-1); // -1 because we add the comment variables
  s+="//variables\n"+*var+"\n";
  delete var;
}

void aalang_cpp::set_istate(std::string* ist,const char* file,int line,int col)
{
  if (ist) {
    istate=new std::string(to_line(file,line)+*ist);
    delete ist;
  }
}

void aalang_cpp::set_ainit(std::string* iai,const char* file,int line,int col)
{
  if (iai) {
    ainit=new std::string(to_line(file,line)+*iai);
    delete iai;
  }
}

void aalang_cpp::set_aexit(std::string* iai,const char* file,int line,int col)
{
  if (iai) {
    aexit=new std::string(to_line(file,line)+*iai);
    delete iai;
  }
}

void aalang_cpp::parallel(bool start) {

  if (start) {
    inner_stack.push(current_inner);
    current_inner=0;

    outter_stack.push(current_outter);
    outters++;
    current_outter=outters;
    inner_names.resize(outters);

    s=s+"struct {\n"
      "std::map<std::string,bool> pos;\n"
      "std::map<int,std::string> name;\n"
      "} outer" + to_string(current_outter) + ";\n";
  } else {

    std::string varname = 
      "outer"+to_string(current_outter)+".pos";
    
    s=s+"void outer_body" + to_string(current_outter) + "(const std::string& name) {\n" +
      varname + "[name]=true;\n" +
      "if ("+varname+".size()=="+to_string(current_inner)+") {\n" +
      varname+".clear();\n"
      "}\n"
    "}\n";

    s=s+"bool outer_guard" + to_string(current_outter) + "(const std::string& name) {\n" +
      "return !" + varname + "[name];\n"
   "}\n";

    current_outter=outter_stack.top();
    outter_stack.pop();

    current_inner=inner_stack.top();
    inner_stack.pop();
  }

}

void aalang_cpp::serial(bool start) {

  if (start) {
    inner_stack.push(current_inner);
    current_inner=0;

    outter_stack.push(current_outter);
    outters++;
    current_outter=outters;
    inner_names.resize(outters);

    s=s+"struct {\n"
      "int pos;\n"
      "std::map<int,std::string> name;\n"
      "} outer" + to_string(current_outter) + ";\n";
  } else {
    std::string varname = 
      "outer"+to_string(current_outter)+".pos";
    std::string nametlb =
      "outer"+to_string(current_outter)+".name";
    
    s=s+"void outer_body" + to_string(current_outter) + "(const std::string& name) {\n" +
      varname + "=(" + varname + "+1)%" + to_string(current_inner) + ";\n"
    "}\n";

    s=s+"bool outer_guard" + to_string(current_outter) + "(const std::string& name) {\n" +
      "return " + nametlb + "[" + varname + "] == name;\n"
    "}\n";

    current_outter=outter_stack.top();
    outter_stack.pop();
  }

}

void aalang_cpp::set_push(std::string* p,const char* file,int line,int col)
{
  push=to_line(file,line)+*p;
  delete p;
}

void aalang_cpp::set_pop(std::string* p,const char* file,int line,int col)
{
  pop=to_line(file,line)+*p;
  delete p;
}

void aalang_cpp::set_tagname(std::string* name,bool first)
{
  if (first) {
    name_cnt_stack.push_back(tag_cnt);
    name_cnt_stack.push_back(name_cnt);
    name_cnt=0;
    tstack.push_back(tag);
    tag_cnt=tname.size();
  }

  if (name_cnt==0) {
    guard_call_construct.push_back("tag"+to_string(tag_cnt)+"_guard(tag_names["+to_string(tag_cnt)+"])");
    tag_guard_call.push_back(to_call(guard_call_construct));
  }
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
  tag=tstack.back();
  tstack.pop_back();
  guard_call_construct.pop_back();
  name_cnt=name_cnt_stack.back();
  name_cnt_stack.pop_back();
  tag_cnt=name_cnt_stack.back();
  name_cnt_stack.pop_back();  
}

void aalang_cpp::set_guard(std::string* gua,const char* file,int line,int col)
{
  std::string outer_guard_call;

  if (current_outter != -1) {
    outer_guard_call = "if (!outer_guard" + to_string(current_outter) + "(name)) { return false; }\n";
  }

  if (gua!=&default_guard) {
    *gua="{\n" + *gua + "\n}\n" + default_guard;
  }
  if (tag) {
    s+=to_line(file,line)+"bool tag"+to_string(tag_cnt)+"_guard(const std::string& name) {\n"+
      outer_guard_call+
      *gua+"\n}\n";
  } else {
    s+=to_line(file,line)+"bool action"+to_string(action_cnt)+"_guard(const std::string& name) {\n"+
      outer_guard_call+
      *gua+"\n}\n";
  }
  if (gua!=&default_guard) 
    delete gua;
}

void aalang_cpp::set_body(std::string* bod,const char* file,int line,int col)
{
  std::string outer_body_call;

  if (current_outter != -1) {
    outer_body_call = "outer_body" + to_string(current_outter) + "(name);\n";
  }

  s+=to_line(file,line)+"void action"+to_string(action_cnt)+"_body(const std::string& name) {\n" + outer_body_call +*bod+"\n}\n";
  if (bod!=&default_body) 
    delete bod; 
}

void aalang_cpp::set_adapter(std::string* ada,const char* file,int line,int col)
{
  if (tag) {
    tag_adapter[tag_cnt]=true;
    s+=to_line(file,line)+"int tag" + to_string(tag_cnt) + "_adapter(const std::string& name) {\n{\n" +
      *ada + "\n}\n"
      "\treturn " + to_string(tag_cnt) + ";\n"
      "}\n";    
  } else {
    s+=to_line(file,line)+"int action" + to_string(action_cnt) + "_adapter(const char* param,const std::string& name) {\n{\n" +
      *ada + "\n}\n"
      "\treturn " + to_string(action_cnt) + ";\n"
      "}\n";
  }
  if (ada!=&default_adapter)
    delete ada;
}

void aalang_cpp::next_action()
{
  std::vector<std::string> t;
  aname.push_back(t);
  action_cnt+=name_cnt;
  name_cnt=0;
  tag=tstack.back();
  tstack.pop_back();
  guard_call_construct.pop_back();
  name_cnt=name_cnt_stack.back();
  name_cnt_stack.pop_back();
  action_cnt=name_cnt_stack.back();
  name_cnt_stack.pop_back();  
}

std::string aalang_cpp::stringify()
{
  action_cnt=anames.size();
  tag_cnt=tname.size();
  s=s+
    "\npublic:\n"
    "\tvirtual ~_gen_"+*name+"() {}\n"
    "\t_gen_"+*name+"(Log& l, std::string& _params): aal(l, _params) {\n\taction_names.push_back(\"\");\n";

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

  for(unsigned i=0;i<inner_names.size();i++) {
    int count=1;
    for(std::list<std::string>::iterator j=inner_names[i].begin();j!=inner_names[i].end();j++) {
      s+="\touter"+to_string(i+1)+".name["+to_string(count)+"]="
	"std::string(\""+*j+"\");\n";
      count++;
    }
  }

  s+="}\n";

  if (istate) {
    s+="virtual bool reset() {\n"+
      *istate+
      "\nreturn true;\n}\n\n";
  }

  if (ainit) {
    s+="virtual bool init() {\n"+
      *ainit+
      "\nreturn true;\n}\n\n";
  }

  if (aexit) {
    s+="virtual void adapter_exit(Verdict::Verdict verdict, const std::string& reason) {\n"+
      *aexit+
      "}\n\n";
  }

  if (pop!="") {
    s=s+"\nvirtual void pop(){\n"+pop+"\n}\n";
    s=s+"\nvirtual void push(){\n"+push+"\n}\n";
  }

  s=s+"virtual int observe(std::vector<int>&action, bool block){\n"
    "\taction.clear();\n"
    "\tdo {\n"
    "\tint r=Alphabet::SILENCE;\n";

  int obsa=0;

  for(int i=1;i<action_cnt;i++) {
    if (anames[i][0]=='o') {
      obsa++;
      s=s+"\tr=action"+to_string(amap[i])+"_adapter(NULL,action_names["+to_string(i)+"]);\n"
	"\tif (r) { action.push_back(r); return 1;}\n";
    }
  }
  if (!obsa) {
    s=s+"\treturn r;\n";
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
	"_adapter(param,action_names["+to_string(i)+"]);\n\t\tbreak;\n";
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
      "\t\taction"+to_string(amap[i])+"_body(action_names["+to_string(i)+"]);\n\t\treturn "+
      to_string(i)+";\n\t\tbreak;\n";
  }
  s=s+"\t\tdefault:\n"
    "\t\treturn 0;\n"
    "\t};\n"
    "}\n"
    "virtual int getActions(int** act) {\n"
    "actions.clear();\n";
  
  for(int i=1;i<action_cnt;i++) {
    s+="\tif ( " + action_guard_call[i-1] + ") {\n"
     "\t\tactions.push_back("+to_string(i)+");\n"
      "\t}\n";
  }
  s=s+"\t*act = &actions[0];\n"
    "\treturn actions.size();\n"
    "}\n";
  
  s=s+"virtual int check_tags(std::vector<int>& tag,std::vector<int>& t) {\nt.resize(0);\n";

  for(int i=0;i<tag_cnt;i++) {
    if (tag_adapter[i]) {

      std::string tnr=to_string(i);
      s=s+"if (std::find(tag.begin(),tag.end(),"+tnr+")!=tag.end()) {\n"
	"// Tag"+tnr+" adapter\n"+
	"if (!tag"+tnr+"_adapter(tag_names["+tnr+"])) {\n"+
	"  t.push_back("+tnr+");\n"+
	"}\n"+
	"}\n";
    }
  }

  s=s+"\nreturn t.size();\n}\n";

  s=s+"virtual int getprops(int** props) {\n"
    "\ttags.clear();\n";

  for(int i=1;i<tag_cnt;i++) {
    s+="\tif ( " + tag_guard_call[tmap[i]-1] + ") {\n"
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
    "aal* al_helper(Log&l, std::string& params) {\n"
    "  if (aal::storage==NULL) {\n"
    "	aal::storage=new std::map<std::string,aal*>;\n"
    "  }\n"
    "  aal* al=(*aal::storage)[\""+*name+"\"];\n"
    "  if (!al){\n"
    "   al=new _gen_"+*name+"(l,params);\n"
    "	(*aal::storage)[\""+*name+"\"]=al;\n"
    "  }\n"
    "  return al;\n"
    "}\n"
    "Model* model_creator(Log&l, std::string params) {\n"
    "\taal* al=al_helper(l,params);\n"
    "\treturn new Mwrapper(l,params,al);\n"
    "}\n\n"
    "static ModelFactory::Register me1(\""+*name+"\", model_creator);\n\n"
    "Adapter* adapter_creator(Log&l, std::string params = \"\")\n"
    "{\n"
    "\taal* al=al_helper(l,params);\n"
    "\treturn new Awrapper(l,params,al);\n"
    "}\n"
    "static AdapterFactory::Register me2(\""+*name+"\", adapter_creator);\n"+
    "}\n";
}
