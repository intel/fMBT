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

#include "lts.hh"
#include "dparse.h"
#include <inttypes.h>

#include "helper.hh"
#include <cstdlib>
#include <cstdio>
#include <cstring>
#undef max
#undef min
#include <sstream>

#define debugprint(a ...) log.debug(a)

extern "C" {
extern D_ParserTables parser_tables_lts;
};

std::string Lts::stringify()
{
  std::ostringstream t(std::ios::out | std::ios::binary);

  t << "Begin Lsts\nBegin Header\n";

  t << "State_cnt = "      << state_cnt      << std::endl;
  t << "Action_cnt = "     << action_cnt     << std::endl;
  t << "Transition_cnt = " << transition_cnt << std::endl;
  t << "Initial_states = " << init_state;
  t << ";\nEnd Header\n";

  t << "Begin Action_names\n";

  for(int i=1;i<=action_cnt;i++) {
    t << i << " = \"" << action_names[i] << "\"\n";
  } 
  t << "End Action_names\n";

  t << "Begin Transitions\n";

  for(int i=1;i<=state_cnt;i++) {
    t << " " << i << ":";
    for(int j=0;j<state[i].transitions;j++) {
      t << " " << dstate[j+state[i].first] << ","
	<< actions[j+state[i].first];
    }

    t << ";" << std::endl;
    
  }

  t << "End Transitions\n";
  t << "End Lsts\n";
  return t.str();
}

int Lts::getActions(int** _actions)
{
  *_actions=&actions[state[current_state].first];
  
  return state[current_state].transitions;
}

int Lts::getIActions(int** _actions)
{
  *_actions=&actions[state[current_state].first];
  return state[current_state].transitions-state[current_state].otransitions;

}

extern Lts* obj;

bool Lts::load(std::string& name)
{
  D_Parser *p = new_D_Parser(&parser_tables_lts, 512);
  char *s;
  Lts* tmp=obj;
  bool ret;

  debugprint("Lts::load %s",name.c_str());

  obj=this;

  s=readfile(name.c_str());

  if (s==NULL) {
    debugprint("Can't load lts %s",name.c_str());
    throw (int)(42011);
  }

  ret=dparse(p,s,std::strlen(s));

  if (ret) {
    debugprint("Loading of %s ok\n",name.c_str());
  } else {
    debugprint("Loading of %s failed\n",name.c_str());
    status=false;
  }
  free(s);

  free_D_Parser(p);

  obj=tmp;

  return ret;
}

bool Lts::reset()
{
  current_state=init_state;
  return true;
}

bool Lts::header_done()
{
  
  action_names.resize(action_cnt+1); // TAU
  
  actions.reserve(transition_cnt+1);
  dstate.reserve(transition_cnt+1);
  
  state.resize(state_cnt+1);

  return true;
}

#include <iostream>

void Lts::add_action(int number,std::string& name)
{
  action_names[number]=name;
  /* We suck.. sucess */
}

void Lts::add_transitions(int st,
			  std::vector<int>& oa,
			  std::vector<int>& ia,
			  std::vector<int>& os,
			  std::vector<int>& is)
{

  debugprint("Updating state %i",
	 st);

  state[st].first=actions.size();
  state[st].transitions=oa.size()+ia.size();
  state[st].otransitions=oa.size();

  actions.insert(actions.end(),oa.begin(),oa.end());
  actions.insert(actions.end(),ia.begin(),ia.end());

  dstate.insert(dstate.end(),os.begin(),os.end());
  dstate.insert(dstate.end(),is.begin(),is.end());
}

int Lts::execute(int action)
{
  struct _state* st=&state[current_state];
  
  debugprint("Lts::execute: trying to execute action %i at state %i",action,current_state);
  
  debugprint("%i %i",
	 st->first,
	 st->transitions);
  
  for(int i=0;i<st->transitions;i++) {
    debugprint("state[%i] action %i",
	   current_state,actions[st->first+i]);
    if (actions[st->first+i]==action) {
      current_state=dstate[st->first+i];
      debugprint("Lts::execute: action found, continuing from state %i",current_state);
      return true;
    }
  }
  debugprint("Lts::execute: can't execute");
  return false;
}

namespace {
  Model* lts_creator(Log&l) {
    return new Lts(l);
  }
  static model_factory lts_foo("lts",lts_creator);
  static model_factory lsts_foo("lsts",lts_creator);
};
