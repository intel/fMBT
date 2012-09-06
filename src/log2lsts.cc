/*
 * fMBT, free Model Based Testing tool
 * Copyright (c) 2011,2012 Intel Corporation.
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
#include "log_null.hh"
#include "history_log.hh"
#include "coverage.hh"

class ltscoverage: public Coverage {
public:
  ltscoverage(Log&l,History_log& _h): Coverage(l), prop_count(0), lts(l), hl(_h)
  {}
  virtual ~ltscoverage() {}
  virtual void push() {}
  virtual void pop() {}
  virtual bool execute(int action) {return true;}
  virtual float getCoverage() { return 0.0;}
  virtual int fitness(int* actions,int n, float* fitness) { return 0;}

  virtual void history(int action, std::vector<int>& props,
 		       Verdict::Verdict verdict)
  {
    // implementation....
    if (action) {
      trace.push_back(action);

      if (prop.size()<hl.tnames.size()) {
	prop.resize(hl.tnames.size());
      }
      
      for(unsigned i=0;i<props.size();i++) {
	prop[props[i]].push_back(trace.size());
      }
    } else {
      // verdict. Let's create lts.
      // We might have props...

      for(unsigned i=0;i<props.size();i++) {
	prop[props[i]].push_back(trace.size()+1);
      }

      lts.set_state_cnt(trace.size()+1);
      lts.set_action_cnt(hl.anames.size()-1);
      lts.set_transition_cnt(trace.size());
      lts.set_prop_cnt(hl.tnames.size()-1);
      lts.set_initial_state(1);
      lts.header_done();

      for(unsigned i=1;i<hl.anames.size();i++) {
	lts.add_action(i,hl.anames[i]);
      }

      for(unsigned i=0;i<trace.size();i++) {
	std::vector<int> e;
	std::vector<int> a;
	std::vector<int> s;
	a.push_back(trace[i]);
	s.push_back(i+2);
	lts.add_transitions(i+1,a,e,s,e);
      }
      for(unsigned i=1;i<prop.size();i++) {
	lts.add_prop(&hl.tnames[i],prop[i]);
      }
    }
  }

  std::vector<int> trace;
  std::vector<std::vector<int> > prop;
  int prop_count;
  Lts lts;
  History_log& hl;
};

int main(int argc,char * const argv[])
{
  Log_null log;

  std::string file(argv[1]);

  History_log hl(log,file);

  ltscoverage cov(log,hl);

  hl.set_coverage(&cov,NULL);

  printf("%s\n",cov.lts.stringify().c_str());
}
