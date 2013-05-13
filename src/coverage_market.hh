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

/* Coverage_Market measures coverage requirement based on a coverage
 * language. Coverage requirements are given as a parameter. For
 * syntax refer to requirements.g.
 */

#ifndef __coverage_market_hh__
#define __coverage_market_hh__

#include <stack>

#include "coverage.hh"

#include <map>
#include <vector>

#include <cstdlib>

#define MAX(a,b) (((a)>(b))?(a):(b))
#define MIN(a,b) (((a)<(b))?(a):(b))

#include "coverage_tree.hh"
#include "log_null.hh"
#include "helper.hh"

class Model;

class Coverage_Market;
extern Coverage_Market* cobj;

class Coverage_Market: public Coverage {

public:
  class unit;
  Coverage_Market(Log& l, std::string& _params);
  virtual ~Coverage_Market() {
    for(size_t i=0;i<Units.size();i++) {
      delete Units[i];
    }
  }

  virtual void push() {
    for (unsigned int i = 0; i < Units.size(); i++) Units[i]->push();
  };
  virtual void pop() {
    for (unsigned int i = 0; i < Units.size(); i++) Units[i]->pop();
  };

  virtual void history(int action, std::vector<int>& props,
                       Verdict::Verdict verdict);
  virtual bool execute(int action);
  virtual float getCoverage();

  virtual int fitness(int* actions,int n, float* fitness);

  Model* get_model()
  {
    return model;
  }

  virtual void set_model(Model* _model)
  {
    model=_model;
    add_requirement(params);
  }

  void add_requirement(std::string& req);

  unit* req_rx_action(const char m,const std::string &action);

  void add_unit(unit* u) {
    Units.push_back(u);
  }

  /**
   * coveragerequirement
   *
   * (a action1 or e action2) and action3 then ((action4 or action5) not action1)
   *
   */


  typedef std::pair<int, int> val;

  class unit {
  public:
    val& get_value() {
      return value;
    }
    virtual ~unit() {value.first=0;value.second=0;}
    virtual void execute(int action)=0;
    virtual void update()=0;
    virtual void push()=0;
    virtual void pop()=0;
    virtual void reset() {}
    val value;
  };

  class unit_perm: public unit {
  public:
    unit_perm(int i,Coverage_Market* _m) {
      p=to_string(i);
      m=_m;
      reset();
      /*
      child=new Coverage_Tree(l,p);
      child->set_model(m->get_model());
      value.second=child->max_count;
      */
      l.ref();
    }
    virtual ~unit_perm() {
      delete child;
    }
    virtual void push()
    {
      child->push();
      child_save.push(child);
    }
    virtual void pop()
    {
      child->pop();
      if (child_save.top()!=child) {
	delete child;
	child=child_save.top();
      }
      child_save.pop();
    }
    virtual void reset()
    {
      if (!child_save.empty() && child_save.top()!=child) {
	delete child;
      }
      child=new Coverage_Tree(l,p);
      child->set_model(m->get_model());
      value.second=child->max_count;
    }
    virtual void update()
    {
      value.first=child->node_count-1;
      value.second=child->max_count;
    }
    virtual void execute(int action)
    {
      child->execute(action);
    }
    Log_null l;
    Coverage_Tree* child;
    std::stack<Coverage_Tree*> child_save;
    Coverage_Market* m;
    std::string p;
  };

  class unit_walk: public unit {
  public:
    unit_walk(unit* c,bool _min):child(c),count(0),minimi(_min) {
      push_depth=0;
    }
    virtual ~unit_walk() {
      delete child;
    }

    void minimise() {
      bool child_update_needed=true;
      sexecuted.push(executed);
      while (executed.size()>1) {
	// vector pop_front
	executed.erase(executed.begin());
	if (child_update_needed) {
	  child->push();
	  child->reset();
	}
	child->execute(executed[0]);
	child->update();
	if (child->get_value().first>0) {
	  child_update_needed=true;
	  for(unsigned i=1;i<executed.size();i++) {
	    child->execute(executed[i]);
	  }
	  child->update();
	  val v=child->get_value();
	  if (v.first==v.second) {
	    // New minimal trace!
	    sexecuted.pop();
	    sexecuted.push(executed);
	  }
	  child->pop();      
	} else {
	  child_update_needed=false;
	}
      }
      if (!child_update_needed) {
	child->pop();
      }
      executed=sexecuted.top();
      sexecuted.pop();
    }

    virtual void execute(int action) {
      bool added=false;

      child->update();
      val tmp=child->get_value();
      if (tmp.first>0) {
	executed.push_back(action);
	added=true;
      }
      child->execute(action);
      child->update();
      tmp=child->get_value();

      if (tmp.first>0 && !added) {
	executed.push_back(action);
	added=true;
      }
      
      if (tmp.first==tmp.second) {
	if (!added) {
	  executed.push_back(action);
	}

	// minimise...

	if (minimi) {
	  minimise();
	}

	if (push_depth!=0 && 
	    tcount_save[push_depth-1][executed]==0) {
	  tcount_save[push_depth-1][executed]=tcount[executed];
	}

	tcount[executed]++;
	executed.clear();
	child->reset();
	value=tmp;
	value.first=0;
      } else {
	value=tmp;
      }
      value.first+=tcount.size()*value.second;
    }

    virtual void update() {
      child->update();
      value=child->get_value();
      value.first+=(tcount.size()-count)*value.second;
    }

    virtual void reset() {
      child->reset();
      count=tcount.size();
    }

    virtual void push() {
      push_depth++;
      tcount_save.resize(push_depth);
      child->push();
      st.push(count);
      sexecuted.push(executed);
      //tcount_save.push(tcount);
    }

    virtual void pop() {
      child->pop();
      count=st.top();
      st.pop();
      executed=sexecuted.top();
      sexecuted.pop();

      push_depth--;
      std::map<std::vector<int >, int>::iterator i;
      std::map<std::vector<int >, int>::iterator e;
      i=tcount_save[push_depth].begin();
      e=tcount_save[push_depth].end();
      for(;i!=e;i++) {
	if (i->second) {
	  tcount[i->first] = i->second;
	} else {
	  tcount.erase(i->first);
	}
      }
      tcount_save.resize(push_depth);
    }
  protected:
    unsigned push_depth;
    unit* child;
    unsigned count;
    std::stack<unsigned> st;
    std::vector<int> executed;
    std::stack<std::vector<int> > sexecuted;

    std::map<std::vector<int >, int> tcount;
    std::vector<std::map<std::vector<int >, int> > tcount_save;
    bool minimi;
  };

  class unit_many: public unit {
  public:
    unit_many() {}
    virtual ~unit_many() {
      for(size_t i=0;i<units.size();i++) {
	delete units[i];
      }
    }

    virtual void reset() {
      for(size_t i=0;i<units.size();i++) {
	units[i]->reset();
      }
    }

    virtual void push() {
      for(size_t i=0;i<units.size();i++) {
	units[i]->push();
      }
    }

    virtual void pop() {
      for(size_t i=0;i<units.size();i++) {
	units[i]->pop();
      }
    }

    virtual void update() {
      for(size_t i=0;i<units.size();i++) {
	units[i]->update();
      }
    }

    virtual void execute(int action) {
      for(size_t i=0;i<units.size();i++) {
	units[i]->execute(action);
      }
    }
    std::vector<unit*> units;
  };

  class unit_manyleaf: public unit {
  public:
    unit_manyleaf() {}
    virtual ~unit_manyleaf() {}

    virtual void reset() {
      unit::value.first=0;
      for(unsigned i=0;i<value.size();i++) {
	value[i]=0;
      }
    }

    virtual void push() {
      st.push(value);
      st2.push(unit::value);
    }

    virtual void pop() {
      value=st.top();
      st.pop();
      unit::value=st2.top();
      st2.pop();
    }

    virtual void update() {
    }

    /*
    virtual void execute(int action) {
      for(unsigned i=0;i<my_action.size();i++) {
	if (action==my_action[i]) {
	  if (value[i]<unit::value.second) {
	    value[i]++;
	  }
	}
      }
    }
    */

    std::vector<int> my_action;
    std::vector<int> value;
    std::stack<std::vector<int> > st;
    std::stack<val> st2;
  };

  class unit_manyleafand: public unit_manyleaf {
  public:
    unit_manyleafand() {}
    virtual ~unit_manyleafand() {}

    virtual void execute(int action) {
      if (unit::value.first==unit::value.second) {
	return;
      }
      for(unsigned i=0;i<my_action.size();i++) {
	if (action==my_action[i]) {
	  if (value[i]<1) {
	    value[i]++;
	    unit::value.first++;
	    return;
	  }
	}
      }
    }
    /*
    virtual void update(){
      unit::value.first=0;

      for(size_t i=0;i<value.size();i++) {
	unit::value.first += value[i];
      }
    }
    */

  };

  class unit_manyleafor: public unit_manyleaf {
  public:
    unit_manyleafor() {}
    virtual ~unit_manyleafor() {}

    virtual void execute(int action) {
      if (unit::value.first==unit::value.second) {
	return;
      }
      for(unsigned i=0;i<my_action.size();i++) {
	if (action==my_action[i]) {
	  if (value[i]<unit::value.second) {
	    value[i]++;
	    unit::value.first=unit::value.second;
	    return;
	  }
	}
      }
    }

    /*
    virtual void update(){
      for(size_t i=0;i<value.size();i++) {
	if (value[i]) {
	  unit::value.first = unit::value.second;
	  return;
	}
      }
      unit::value.first=0;
    }
    */
  };

  class unit_manyand: public unit_many {
  public: 
    unit_manyand() {}
    virtual ~unit_manyand() {
    }
    virtual void update() {
      units[0]->update();
      value=units[0]->get_value();
      for(size_t i=1;i<units.size();i++) {
	units[i]->update();
	val vr=units[i]->get_value();
	value.first +=vr.first;
	value.second+=vr.second;
      }
    }   
  };

  class unit_manyor: public unit_many {
  public: 
    unit_manyor() {}
    virtual ~unit_manyor() {
    }
    virtual void update() {
      units[0]->update();
      value=units[0]->get_value();
      for(size_t i=1;i<units.size();i++) {
	units[i]->update();
	val vr=units[i]->get_value();
	value.first  =
	  MAX(value.first/value.second,
	      vr.first/vr.second)*(value.second+vr.second);
	value.second+=vr.second;
      }
    }   
  };

  class unit_dual: public unit {
  public:
    unit_dual(unit* l,unit* r):left(l),right(r) {
    }

    virtual void reset() {
      left->reset();
      right->reset();
    }

    virtual void push() {
      left->push();
      right->push();
    }

    virtual void pop() {
      left->pop();
      right->pop();
    }

    virtual ~unit_dual() {
      delete left;
      delete right;
    }

    virtual void execute(int action) {
      left->execute(action);
      right->execute(action);
    }

  protected:
    unit* left,*right;

  };

  class unit_and: public unit_dual {
  public:
    unit_and(unit* l,unit* r) : unit_dual(l,r) {}
    virtual void update() {
      left->update();
      right->update();
      val vl=left->get_value();
      val vr=right->get_value();
      value.first = vl.first+vr.first;
      value.second=vl.second+vr.second;
    }
  protected:
  };

  class unit_or: public unit_dual {
  public:
    unit_or(unit* l,unit* r) : unit_dual(l,r) {}
    virtual void update() {
      left->update();
      right->update();
      val vl=left->get_value();
      val vr=right->get_value();
      /* ???? */
      value.first =
        MAX(vl.first/vl.second,
            vr.first/vr.second)*(vl.second+vr.second);
      value.second=vl.second+vr.second;
    }
  protected:

  };

  class unit_not: public unit {
  public:
    unit_not(unit *c):child(c) {
    }

    virtual void reset() {
      child->reset();
    }

    virtual void push() {
      child->push();
    }

    virtual void pop() {
      child->pop();
    }
    virtual ~unit_not() {
      delete child;
    }
    virtual void execute(int action) {
      child->execute(action);
    }

    virtual void update() {
      child->update();
      val v=child->get_value();
      value.first=v.second-v.first;
      value.second=v.second;
    }
  protected:
    unit* child;
  };

  class unit_then: public unit_many {
  public:
    int cpos;
    std::stack<int> csave;
    unit_then(unit* l,unit* r) {
      unit_then* ut=dynamic_cast<unit_then*>(r);
      cpos=0;
      if (ut) {
	// our right child is a then. We'll add left to the first.
	units.push_back(l);
	units.insert(units.end(),ut->units.begin(),ut->units.end());
	ut->units.clear();
	delete ut;
      } else {
	units.push_back(l);
	units.push_back(r);
      }
    }

    virtual void push() {
      csave.push(cpos);
      unit_many::push();
    }

    virtual void pop() {
      cpos=csave.top();
      csave.pop();
      unit_many::pop();
    }

    virtual void reset()
    {
      cpos=0;
      unit_many::reset();
    }

    virtual void execute(int action) {
      for(size_t i=cpos;i<units.size()-1;i++) {
	units[i]->update();
	val v=units[i]->get_value();	
	if (v.first==v.second) {
	  continue;
	} else {
	  cpos=i;
	  units[i]->execute(action);
	  return;
	}
      }
      cpos=units.size();
      units.back()->execute(action);
    }

    virtual void update() {
      value.first=0;
      value.second=0;
      for(size_t i=cpos;i<units.size();i++) {
	units[i]->update();
	val v=units[i]->get_value();	
	value.first+=v.first;
	value.second+=v.second;
      }
    }
    
  };

  class unit_then_: public unit_dual {
  public:
    unit_then_(unit* l,unit* r) : unit_dual(l,r) {}
    virtual ~unit_then_()  {}
    virtual void execute(int action) {
      // if left, then right
      left->update();
      val v=left->get_value();
      if (v.first==v.second) {
        right->execute(action);
      } else {
        left->execute(action);
      }
    }

    virtual void update() {
      left->update();
      right->update();
      val vl=left->get_value();
      val vr=right->get_value();
      /* ???? */
      value.first=vl.first+vr.first;
      value.second=vl.second+vr.second;
    }
  protected:

  };

  class unit_leaf: public unit {
  public:
    unit_leaf(int action, int count=1) : my_action(action) {
      value.second=count;
    }

    virtual void reset() {
      value.first=0;
    }

    virtual void push() {
      st.push(value);
    }

    virtual void pop() {
      value=st.top();
      st.pop();
    }

    virtual void execute(int action) {
      if (action==my_action) {
        if (value.first<value.second) {
          value.first++;
        }
      }
    }

    virtual void update() {
    }

  protected:
    int my_action;
    std::stack<val> st;
  };

  class unit_mult: public unit {
  public:
    unit_mult(unit* l,int i): max(i),child(l),count(0) {
    }

    virtual void reset() {
      count=0;
    }

    virtual void push() {
      child->push();
      st.push(count);
    }

    virtual void pop() {
      child->pop();
      count=st.top();
      st.pop();
    }

    virtual ~unit_mult() {
      delete child;
    }

    virtual void execute(int action) {
      update();
      if (count<max)
	child->execute(action);
      update();
    }

    virtual void update() {
      child->update();
      val v=child->get_value();
      if (v.first==v.second) {
	child->reset();
	child->update();
	count++;
      }
      value.second=max*v.second;
      value.first=count*v.second+v.first;

    }
    
    int max;
  protected:
    unit* child;
    int count;
    std::stack<int> st;
  };

protected:
  std::vector<unit*> Units;
  std::string params;
};


#endif
