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

  for(unsigned i=0;i<actions->size();i++) {
    if ((*actions)[i]!="") {
      const char* s=(*actions)[i].c_str();

      if (strncmp(s,"iSetTimer ",strlen("iSetTimer "))==0) {
	/* Set Timer */
	char* endp;
	unsigned timer=strtol(s+strlen("iSetTimer "),&endp,10);

	if (timeout.size()<=timeout.size()) {
	  timeout.resize(timer+1);
	}

	double time=strtod(endp+1,NULL);

	atime[timer].timer=timer;
	atime[timer].time.tv_sec=trunc(time);
	atime[timer].time.tv_usec=1000000*(time-trunc(time));
      }

      if (strncmp(s,"iClearTimer ",strlen("iClearTimer "))==0) {
	/* Clear Timer */
	unsigned timer=atoi(s+strlen("iClearTimer "));

	if (timeout.size()<=timeout.size()) {
	  timeout.resize(timer+1);
	}

	clear_map[i]=timer;
      }

      if (strncmp(s,"oTimeout ",strlen("oTimeout "))==0) {
	unsigned timer=atoi(s+strlen("oTimeout "));	
	if (timeout.size()<=timeout.size()) {
	  timeout.resize(timer+1);
	}
	expire_map[timer]=i;
      }

    }

  }

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

  struct action_timeout& at=atime[action[0]];

  //at.timer;

  timeradd(&at.time,&current_time,&timeout[at.timer]);

  log.pop();
}

bool Adapter_timer::observe(std::vector<int> &action,
			    bool block)
{
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
