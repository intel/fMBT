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

      if (strncmp(s,"iSleep ",strlen("iSleep "))==0) {
	sleep_time[i]=atoi(s+strlen("iSleep "));
      }

      if (strncmp(s,"iSetTimer ",strlen("iSetTimer "))==0) {
	/* Set Timer */
	char* endp;
	unsigned timer=strtol(s+strlen("iSetTimer "),&endp,10);

	if (timeout.size()<=timeout.size()) {
	  timeout.resize(timer+1);
	}

	double time=strtod(endp+1,NULL);

	atime[i].timer=timer;
	atime[i].time.tv_sec=trunc(time);
	atime[i].time.tv_usec=1000000*(time-trunc(time));
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
	log.print("<timer id=%i,action=%i name=\"%s\"/>\n",
		  timer,i,s);
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

void Adapter_timer::clear_timer(int timer)
{
  int pos=-1;
  for(unsigned i=0;i<enabled.size() && pos==-1;i++) {
    if (enabled[i]==timer) {
      pos=i;
    }
  }
  if (pos>0) {
    enabled.erase(enabled.begin()+pos);
  }
}

/* adapter can execute.. */
void Adapter_timer::execute(std::vector<int>& action)
{
  log.push("Adapter_timer");

  struct action_timeout& at=atime[action[0]];

  log.print("<action type=\"input\" name=\"%s\" timer=%i/>\n",
	    getUActionName(action[0]),at.timer);

  if (!isInputName((*actions)[action[0]])) {
    abort();
  }

  if (sleep_time[action[0]]) {
    sleep(sleep_time[action[0]]);
    log.pop();
    action.resize(1);
    return;
  }

  if (at.timer>0) {
    unsigned i;
    log.print("<we have a timeradd %i/>\n",at.timer);
    
    timeradd(&at.time,&current_time,&timeout[at.timer]);
    /* Let's enable the timer.. */
    for(i=0;i<enabled.size() && enabled[i]!=at.timer;i++) { }
    if (i==enabled.size()) {
      enabled.push_back(at.timer);
    }
    for(i=0;i<enabled.size();i++) {
      log.print("<timer enabled=%i expire %i.%06i/>\n",
		enabled[i],
		timeout[enabled[i]].tv_sec,
		timeout[enabled[i]].tv_usec
		);
    }
  } else {
    int timer=clear_map[action[0]];
    log.print("<we have a timerclean %i/>\n",timer);
    if (timer>0) {
      clear_timer(timer);
    }
  }
  
  log.pop();
}

bool Adapter_timer::observe(std::vector<int> &action,
			    bool block)
{
  for(unsigned i=0;i<enabled.size();i++) {
    int timer_id=enabled[i];
    if (timer_id) {
      struct timeval* tv=&timeout[timer_id];
      if (!timercmp(&current_time,tv,<)) {
	/* expire */
	clear_timer(timer_id);
	action.resize(1);
	action[0]=expire_map[timer_id];
	log.print("<timer_expire id=%i, action=%i, name=\"%s\"/>\n",
		  timer_id,action[0],
		  (*actions)[action[0]].c_str()
		  );
	return true;
      }
    }
  }
  return false;
}

FACTORY_DEFAULT_CREATOR(Adapter, Adapter_timer, "timer");
