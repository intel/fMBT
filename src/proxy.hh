/*
 * fMBT, free Model Based Testing tool
 * Copyright (c) 2012, Intel Corporation.
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

#ifndef __proxy_hh__
#define __proxy_hh__

#include <map>
#include <string>

class Proxy {
public:
  Proxy() {}
  virtual ~Proxy() {
  }

  typedef bool (Proxy::*func_ptr_t)(std::string,std::string&);
protected:
  typedef std::pair<Proxy*,func_ptr_t> pa;
  std::map<std::string,pa> tbl;
public:

  void add_call(std::string name,Proxy*p,func_ptr_t f) {
    tbl[name]=pa(p,f);
  }

  bool call(std::string name,std::string& ret_str) {
    std::map<std::string,pa>::iterator it = tbl.find(name);
    std::string params;

    if (it==tbl.end()) {
      // Not found. Let's try prefix.
      std::size_t pos=name.find_first_of(".(");
      if (pos!=std::string::npos) {
	// Let's cut it baby
	std::string nname=name.substr(0,pos);
	it=tbl.find(nname);
	if (it!=tbl.end()) {
	  params=name.substr(pos+1);
	  return (it->second.first->*it->second.second)(params,ret_str);
	}
      }
    } else {
      return (it->second.first->*it->second.second)(params,ret_str);
    }
    return false;
  }

};

#endif
