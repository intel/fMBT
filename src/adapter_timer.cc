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
#include "adapter_timer.hh"
#include <cstdio>
#include <sstream>

Adapter_timer::Adapter_timer(Log& l,std::string params): Adapter::Adapter(l)
{
  
}

void Adapter_timer::set_actions(std::vector<std::string>* _actions)
{
  /* handle actions... */
  Adapter::set_actions(_actions);
}
std::string Adapter_timer::stringify()
{
  std::ostringstream t(std::ios::out | std::ios::binary);

  t << "timer";

  return t.str();
}

/* adapter can execute.. */
void Adapter_timer::execute(std::vector<int>& action)
{
  log.push("Adapter_timer");

  log.print("<action type=\"input\" name=\"%s\"/>\n",
	    getUActionName(action[0]));

  

  log.pop();
}

bool Adapter_timer::observe(std::vector<int> &action,
			    bool block)
{
  return false;
  for(unsigned i=0;i<enabled.size();i++) {
    int pos=enabled[i];
    if (pos) {
      struct timeval* tv=&timeout[pos];
      if (!timercmp(&current_time,tv,<)) {
	/* expire */
	enabled[i]=0;
	action.resize(1);
	if (expire_map[pos]) {
	  action[0]=expire_map[pos];
	} else {
	  action[0]=0;
	}
	return true;
      }
    }
  }
  return false;
}

FACTORY_DEFAULT_CREATOR(Adapter, Adapter_timer, "timer");
