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
#ifndef __lts_hh__
#define __lts_hh__

#include <vector>
#include <list>
#include <string>
#include <fstream>

#include "model.hh"
#include "log.hh"

class Lts: public Model {
public:
  Lts(Log&l,const std::string& params):
    Model(l, params), state_cnt(0),action_cnt(0),transition_cnt(0),prop_cnt(0),init_state(0) {}
  virtual ~Lts();

  virtual int getActions(int** actions);
  virtual int getIActions(int** actions);

  virtual bool reset();
  virtual int getprops(int** props);
  virtual int  execute(int action);
  virtual void push();
  virtual void pop();

  virtual bool init();

  virtual void add_prop(std::string* name,std::vector<int>& pr);

  bool header_done();
  
  void set_state_cnt(int count) {
    log.debug("state count is %i\n",count);
    state_cnt=count;
  }

  void set_action_cnt(int count) {
    action_cnt=count;
  }

  void set_transition_cnt(int count) {
    transition_cnt=count;
  }

  void set_prop_cnt(int count) {
    prop_cnt=count;
  }

  void set_initial_state(int state)
  {
    init_state=state;
  }

  void add_action(int number,std::string& name);

  void add_transitions(int st,
		       std::vector<int>& oa,
		       std::vector<int>& ia,
		       std::vector<int>& os,
		       std::vector<int>& is);

  virtual std::string stringify();

protected:
  std::map<int,std::vector<int> > stateprops;

  void new_state();

  bool start(std::string s);
  bool end(std::string s);

  std::vector<int> dstate; /* destination states */
  /* actions + dstate describes transitions
   * We'll keep thes 'sorted' so that from each state all output actions are before input 
   * actions 
   */
  
  
  struct _state {
    int first;       /* index to first output transition */
    int transitions; /* how many transition each state has */
    int otransitions; /* how many output transition each state has */
  };
  
  std::vector<struct _state> state;
  std::vector<int> actions;
  std::stack<int> state_save;

  int current_state;                /* current state... */

  int state_cnt;
  int action_cnt;
  int transition_cnt;
  int prop_cnt;
  int init_state;

  std::ifstream input;

  void update_cur();
  bool pair(std::string& start,std::string& end);
  std::string lts_name;
};

#endif

