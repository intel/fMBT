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

void aalang_cpp::set_name(std::string* name)
{
  /*

    { printf("\n\t//action%i: ",action); }

    anames.push_back(*$2.str); printf("%s",$2.str->c_str()); delete $2.str; $2.str=NULL; } ;
  */
  s+="\n\t//action"+to_string(action_cnt)+": "+*name+"\n";
  aname.push_back(*name);
}

void aalang_cpp::set_namestr(std::string* _name)
{ 
  /*
  printf("class _gen_"); 
  printf("%s: public aal {\nprivate:\n\t", 
	 $1.str->c_str()); };
  */
  name=_name;
  s+="#include \"aal.hh\"\n\n";
  s+="class _gen_"+*name+":public aal {\nprivate:\n\t";
}

void aalang_cpp::set_variables(std::string* var)
{
  /*
    printf("//variables\n%s\n",$2.str->c_str()); } ;
  */
  s+="//variables\n"+*var+"\n";
  delete var;
}

void aalang_cpp::set_istate(std::string* ist)
{
  istate=ist;
}

void aalang_cpp::set_guard(std::string* gua)
{
  /*
    printf("bool action%i_guard() {\n%s}\n",action,$3.str->c_str()); } ;
  */
  s+="bool action"+to_string(action_cnt)+"_guard() {\n"+
    *gua+"}\n";
  delete gua;
}

void aalang_cpp::set_body(std::string* bod)
{
  /*
    printf("void action%i_body() {\n%s}\n",action,$3.str->c_str()); } ;
  */
  s+="void action"+to_string(action_cnt)+"_body() {\n"+*bod+"}\n";
  delete bod;
}

void aalang_cpp::set_adapter(std::string* ada)
{
  /*
  printf("int action%i_adapter() {\n%s}\n",action,$3.str->c_str()); }|;
  */
  s+="int action"+to_string(action_cnt)+"_adapter() {\n"+*ada+"}\n";
  delete ada;
}

void aalang_cpp::next_action()
{
  action_cnt++;
}

std::string aalang_cpp::stringify()
{
  s=s+
    "public:\n"
    "\t_gen_"+*name+"() {\n\taction_names.push_back(\"\");\n";

  for(unsigned i=0;i<aname.size();i++) {
    s+="\taction_names.push_back(\""+aname[i]+"\");\n";
  }
  
  s+=*istate+"}\n"
    "virtual int adapter_execute(int action) {\n"
    "\tswitch(action) {\n";

  for(int i=1;i<action_cnt;i++) {
    s+="\t\tcase "+to_string(i)+":\n"
      "\t\treturn action"+to_string(i)+
      "_adapter();\n\t\tbreak;\n";
  }
  s=s+"\t\tdefault:\n"
    "\t\treturn 0;\n"
    "\t};\n"
    "}\n"
    "virtual int model_execute(int action) {\n"
    "\tswitch(action) {\n";

  for(int i=1;i<action_cnt;i++) {
    s+="\t\tcase "+to_string(i)+":\n"
      "\t\taction"+to_string(i)+"_body();\n\t\treturn "+
      to_string(i)+";\n\t\tbreak;\n";
  }
  s=s+"\t\tdefault:\n"
    "\t\treturn 0;\n"
    "\t};\n"
    "}\n"
    "virtual int getActions(int** act) {\n"
    "actions.clear();\n";
  
  for(int i=1;i<action_cnt;i++) {
    s+="\tif (action"+to_string(i)+"_guard()) {\n"
      "\t\tactions.push_back("+to_string(i)+");\n"
      "\t}\n";
  }
  s=s+"\t*act=&actions[0];\n"
    "\treturn actions.size();\n"
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
    "Model* mcreator(Log&l, std::string params) {\n"
    "\tif (!a) {\n"
    "\t  a=new _gen_"+*name+"();\n"
    "\t}\n"
    "\treturn new Mwrapper(l,params,a);\n"
    "}\n\n"
    "static ModelFactory::Register me1(\""+*name+"\", mcreator);\n\n"
    "Adapter* creator_func(Log&l, std::string params = \"\")\n"
    "{\n"
    "\tif (!a) {\n"
    "\t  a=new _gen_"+*name+"();\n"
    "\t}\n"
    "\treturn new Awrapper(l,params,a);\n"
    "}\n"
    "static AdapterFactory::Register me2(\""+*name+"\", creator_func);\n"+
    "};\n";
  
};

