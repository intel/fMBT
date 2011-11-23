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

void aalang_cpp::set_namestr(std::string* name)
{ 
  /*
  printf("class _gen_"); 
  printf("%s: public aal {\nprivate:\n\t", 
	 $1.str->c_str()); };
  */
  s+="class _gen_"+*name+":public aal {\nprivate:\n\t";
}

void aalang_cpp::set_variables(std::string* var)
{
  /*
    printf("//variables\n%s\n",$2.str->c_str()); } ;
  */
  s+="//variables\n"+*var+"\n";
}

void aalang_cpp::set_istate(std::string* ist)
{
  
}

void aalang_cpp::set_guard(std::string* gua)
{
  /*
    printf("bool action%i_guard() {\n%s}\n",action,$3.str->c_str()); } ;
  */
  s+="bool action"+to_string(action_cnt)+"guard() {\n"+
    *gua+"}\n";
}

void aalang_cpp::set_body(std::string* bod)
{
  /*
    printf("void action%i_body() {\n%s}\n",action,$3.str->c_str()); } ;
  */
  s+="void action"+to_string(action_cnt)+"_body() {\n"+*bod+"}\n";
}

void aalang_cpp::set_adapter(std::string* ada)
{
  /*
  printf("int action%i_adapter() {\n%s}\n",action,$3.str->c_str()); }|;
  */
  s+="int action"+to_string(action_cnt)+"adapter() {\n"+*ada+"}\n";
}

void aalang_cpp::next_action()
{
  action_cnt++;
}

std::string aalang_cpp::stringify()
{
  return s;
}

