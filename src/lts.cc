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
#include "factory.hh"
#include <inttypes.h>

#include "helper.hh"
#include <cstdlib>
#include <cstdio>
#include <cstring>
#include <sstream>

extern "C" {
extern D_ParserTables parser_tables_lts;
}

Lts::~Lts()
{

}

int Lts::getprops(int** props) {
  int count=stateprops[current_state].size();

  if (props && count) {
    *props=&(stateprops[current_state][0]);
  }

  return count;
}

std::string Lts::stringify()
{
  if (!status) return errormsg;

  std::ostringstream t(std::ios::out | std::ios::binary);

  t << "Begin Lsts\nBegin Header\n";

  t << "State_cnt = "      << state_cnt      << std::endl;
  t << "Action_cnt = "     << action_cnt     << std::endl;
  t << "Transition_cnt = " << transition_cnt << std::endl;

  if (prop_cnt) {
    t << "State_prop_cnt = " << prop_cnt     << std::endl;
  }

  t << "Initial_states = " << init_state;
  t << ";\nEnd Header\n";

  t << "Begin Action_names\n";

  for(int i=1;i<=action_cnt;i++) {
    t << i << " = \"" << action_names[i] << "\"\n";
  }
  t << "End Action_names\n";

  if (prop_cnt) {
    t << "Begin State_props" << std::endl;
    for(unsigned i=0;i<prop_names.size();i++) {
      if (prop_names[i]!="") {
        int c=0;
        t << "\"" << prop_names[i] << "\" : ";
        for(int ii=1;ii<=state_cnt;ii++) {
          for(unsigned j=0;j<stateprops[ii].size();j++) {
            if (stateprops[ii][j]==(int)i) {
              if (c) {
                t << ", ";
              }
              t << ii;
              c++;
            }
          }
        }
        t << ";" << std::endl;
      }
    }

    t << "End State_props" << std::endl;
  }

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

void Lts::add_prop(std::string* name,std::vector<int>& pr)
{
  if (prop_names.empty()) {
    prop_names.push_back("");
  }
  int pro=prop_names.size();
  prop_names.push_back(*name);

  for(unsigned i=0;i<pr.size();i++) {
    stateprops[pr[i]].push_back(pro);
  }
}

bool Lts::init()
{
  const std::string& name = params;
  D_Parser *p = new_D_Parser(&parser_tables_lts, 512);
  p->loc.pathname = name.c_str();
  char *s;
  Lts* tmp=obj;
  bool ret;

  log.debug("Lts::load %s",name.c_str());

  lts_name=name;

  obj=this;

  s=readfile(name.c_str());

  if (s==NULL) {
    errormsg=std::string("Can't load lts \"")+name+std::string("\"");
    status=false;
    return false;
  }

  ret=dparse(p,s,std::strlen(s));

  ret=p->syntax_errors==0 && ret;

  if (ret) {
    log.debug("Loading of %s ok\n",name.c_str());
  } else {
    log.debug("Error in parsing %s\n",name.c_str());
    errormsg = "Parse error in LTS \"" + name + "\"";
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

  log.debug("Updating state %i",
         st);

  state[st].first=actions.size();
  state[st].transitions=oa.size()+ia.size();
  state[st].otransitions=oa.size();

  actions.insert(actions.end(),ia.begin(),ia.end());
  actions.insert(actions.end(),oa.begin(),oa.end());

  dstate.insert(dstate.end(),is.begin(),is.end());
  dstate.insert(dstate.end(),os.begin(),os.end());
}

int Lts::execute(int action)
{
  struct _state* st=&state[current_state];
  
  for(int i=0;i<st->transitions;i++) {
    if (actions[st->first+i]==action) {
      current_state=dstate[st->first+i];
      return true;
    }
  }
  return false;
}

void Lts::push()
{
  state_save.push(current_state);
}

void Lts::pop()
{
  current_state=state_save.top();
  state_save.pop();
}

FACTORY_DEFAULT_CREATOR(Model, Lts, "lts")
FACTORY_DEFAULT_CREATOR(Model, Lts, "lsts")
