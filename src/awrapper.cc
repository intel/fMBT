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

#include "awrapper.hh"
#include <algorithm>
#include "helper.hh"

Awrapper::Awrapper(Log&l, std::string params, aal* _ada):
  Adapter(l, params), ada(_ada) {
  
}

void Awrapper::set_actions(std::vector<std::string>* _actions)
{
  Adapter::set_actions(_actions);

  std::vector<std::string>& wn=ada->getActionNames();

  for(unsigned i=1;i<wn.size();i++) {
    unsigned result=find(*actions,wn[i]);

    ada2aal[i]=result;
    aal2ada[result]=i;
  }

}

void Awrapper::execute(std::vector<int>& action)
{
  /* We need to map.. */

  int tmp=ada->adapter_execute(aal2ada[action[0]]);
  action[0]=ada2aal[tmp];
  action.resize(1);
}

int  Awrapper::observe(std::vector<int> &action,
		       bool block) {
  return false;
}
