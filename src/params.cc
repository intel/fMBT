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
 */

#include "params.hh"

void split(std::string val,std::string& name,
                 std::string& param, const char* s)
{
  size_t cutpos = val.find_first_of(s);

  if (cutpos == val.npos) {
    name  = val;
    param = std::string("");
  } else {
    name  = val.substr(0,cutpos);
    param = val.substr(cutpos+1);
  }
}

void remove_force(std::string& s,char only)
{
  std::string ss("");
  for(unsigned i=0;i<s.size();i++) {
    switch (s[i]) {
    case '\\': {
      if (i+1<s.size()) {
	if (only==0 || s[i+1]==only) {
	  i++;
	}
      }
    }
    default: {
      ss=ss+s[i];
    }
    }
  }
  s=ss;
}

int last(std::string& val,char c)
{
  int pos=val.length();
  for(;pos>0;pos--) {
    if (val[pos]==c && val[pos-1]!='\\') {
      return pos;
    }
  }
  return -1;
}

void param_cut(std::string val,std::string& name,
               std::string& option)
{
  unsigned pos=0;
  for(;pos<val.length();pos++) {
    switch (val[pos]) {
    case '\\': {
      pos++;
      break;
    }
    case '(':
      int lstpos = last(val,')');
      if (lstpos>0) {
        name = val.substr(0,pos);
        remove_force(name);
        option = val.substr(pos+1,lstpos-pos-1);
        //remove_force(option);
      } else {
        // ERROR
      }
      return;
      break;
    }
  }
  name=val;
}

#include <sstream>

std::string to_string(const unsigned t)
{
  std::stringstream ss;
  ss << t;
  return ss.str();
}
