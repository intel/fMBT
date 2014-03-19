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
  class unit_tag;
  Coverage_Market(Log& l,const std::string& _params);
  virtual ~Coverage_Market() {
    for(size_t i=0;i<Units.size();i++) {
      delete Units[i];
    }
  }

  virtual bool set_instance(int instance) {
    for (unsigned int i = 0; i < Units.size(); i++) {
      Units[i]->set_instance(instance,current_instance);
      // Is this actually needed?
      Units[i]->update();
    }
    current_instance=instance;
    return true;
  }

  virtual void push() { 
    next_prev_save.push(prev);
    next_prev_save.push(next);
    for (unsigned int i = 0; i < Units.size(); i++) Units[i]->push();
  };
  virtual void pop() {
    next=next_prev_save.top();
    next_prev_save.pop();

    prev=next_prev_save.top();
    next_prev_save.pop();
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
    int* p;
    int j=model->getprops(&p);
    prev.assign(p,p+j);
  }

  void add_requirement(std::string& req);

  unit* req_rx_action(const char m,const std::string &action,unit_tag* l=NULL,unit_tag* r=NULL);

  unit_tag* req_rx_tag(const std::string &tag);
  
  void add_unit(unit* u) {
    Units.push_back(u);
  }

  std::vector<int> prev,next;

  std::stack<std::vector<int> > next_prev_save;

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
    virtual void execute(const std::vector<int>& prev,int action,const std::vector<int>& next)=0;
    virtual void update()=0;
    virtual void push()=0;
    virtual void pop()=0;
    virtual void reset() {}
    virtual void set_instance(int instance,int current_instance, bool force=false) =0;
    val value;

    class eunit {
    public:
      std::vector<int> prev;
      int action;
      std::vector<int> next;

      inline bool operator< (const eunit& r) const {
	if (action<r.action || prev<r.prev || next<r.next) {
	  return true;
	}
	return false;
      }
      
    };

    virtual void execute(eunit& un) {
      execute(un.prev,un.action,un.next);
    }

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

    virtual void set_instance(int instance,int current_instance, bool force=false) {
      child->set_instance(instance);
    }

    virtual void push()
    {
      child->push();
      child_save.push(child);
    }

    virtual void pop()
    {
      if (child_save.top()!=child) {
	delete child;
	child=child_save.top();
      }
      child->pop();
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

    virtual void execute(const std::vector<int>& prev,int action,const std::vector<int>& next)
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

    virtual void set_instance(int instance,int current_instance, bool force=false) {
      child->set_instance(instance,current_instance,true);
      walk_instance_map[current_instance]=executed;
      executed=walk_instance_map[instance];
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

    virtual void execute(const std::vector<int>& prev,int action,const std::vector<int>& next) {
      bool added=false;

      child->update();
      val tmp=child->get_value();
      if (tmp.first>0) {
	eunit u={prev,action,next};
	executed.push_back(u);
	added=true;
      }
      child->execute(prev,action,next);
      child->update();
      tmp=child->get_value();

      if (tmp.first>0 && !added) {
	eunit u={prev,action,next};
	executed.push_back(u);
	added=true;
      }
      
      if (tmp.first==tmp.second) {
	if (!added) {
	  eunit u={prev,action,next};
	  executed.push_back(u);
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
      std::map<std::vector<eunit >, int>::iterator i;
      std::map<std::vector<eunit >, int>::iterator e;
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

    std::vector<eunit> executed;
    std::stack<std::vector<eunit> > sexecuted;

    std::map<std::vector<eunit>, int> tcount;
    std::vector<std::map<std::vector<eunit>, int> > tcount_save;
    bool minimi;

    std::map<int,std::vector<eunit> > walk_instance_map;

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

    virtual void execute(const std::vector<int>& prev,int action,const std::vector<int>& next) {
      for(size_t i=0;i<units.size();i++) {
	units[i]->execute(prev,action,next);
      }
    }
    std::vector<unit*> units;
  };

  class unit_manyleaf: public unit {
  public:
    unit_manyleaf() {}
    virtual ~unit_manyleaf() {}

    virtual void set_instance(int instance,int current_instance, 
			      bool forced=false) {
      if (forced) {
	manyleaf_instance_map[current_instance]=value;
	value=manyleaf_instance_map[instance];
      }
    }
    

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
    virtual void execute(const std::vector<int>& prev,int action,const std::vector<int>& next) {
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
    std::map<int,std::vector<int> > manyleaf_instance_map;
  };

  class unit_manyleafand: public unit_manyleaf {
  public:
    unit_manyleafand() {}
    virtual ~unit_manyleafand() {}

    virtual void execute(const std::vector<int>& prev,int action,const std::vector<int>& next) {
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

    virtual void execute(const std::vector<int>& prev,int action,const std::vector<int>& next) {
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

    virtual void set_instance(int instance,int current_instance, bool force=false) {
      // not implemented..
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

    virtual void set_instance(int instance,int current_instance, bool force=false) {
      // not implemented..
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

    virtual void set_instance(int instance,int current_instance, bool force=false) {
      left ->set_instance(instance,current_instance,force);
      right->set_instance(instance,current_instance,force);      
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

    virtual void execute(const std::vector<int>& prev,int action,const std::vector<int>& next) {
      left->execute(prev,action,next);
      right->execute(prev,action,next);
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

    virtual void set_instance(int instance,int current_instance, bool force=false) {
      child->set_instance(instance,current_instance,force);
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
    virtual void execute(const std::vector<int>& prev,int action,const std::vector<int>& next) {
      child->execute(prev,action,next);
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

    virtual void set_instance(int instance,int current_instance, bool force=false) {
      // not implemented..
    }

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

    virtual void execute(const std::vector<int>& prev,int action,const std::vector<int>& next) {
      for(size_t i=cpos;i<units.size()-1;i++) {
	units[i]->update();
	val v=units[i]->get_value();	
	if (v.first==v.second) {
	  continue;
	} else {
	  cpos=i;
	  units[i]->execute(prev,action,next);
	  return;
	}
      }
      cpos=units.size();
      units.back()->execute(prev,action,next);
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

    virtual void set_instance(int instance,int current_instance, bool force=false) {
      left ->set_instance(instance,current_instance,true);
      right->set_instance(instance,current_instance,true);
    }


    virtual void execute(const std::vector<int>& prev,int action,const std::vector<int>& next) {
      // if left, then right
      left->update();
      val v=left->get_value();
      if (v.first==v.second) {
        right->execute(prev,action,next);
      } else {
        left->execute(prev,action,next);
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

  class unit_tag : public unit {
  public:
    unit_tag() {
    }

    virtual ~unit_tag() { }
    virtual void set_left(bool l) {
      left_side=l;
    }

    virtual void execute(const std::vector<int>&, int, const std::vector<int>&) {}
    virtual void update() {}
    virtual void push() {}
    virtual void pop() {}
    virtual void set_instance(int, int, bool) {}

  protected:
    bool left_side;
    
  };

  class unit_tagnot: public unit_tag {
  public:
    unit_tagnot(unit_tag* t): child(t) {
      if (child)
	value=child->value;
    }

    virtual ~unit_tagnot() {
      if (child)
	delete child;
    }

    virtual void set_instance(int instance,int current_instance, bool force=false) {
      child->set_instance(instance,current_instance,force);
    }

    virtual void set_left(bool l) {
      unit_tag::set_left(l);
      child->set_left(l);
    }

    virtual void reset() {
      child->reset();
      update();
    }

    virtual void push() {
      child->push();
    }

    virtual void pop() {
      child->pop();
    }

    virtual void execute(const std::vector<int>& prev,int action,const std::vector<int>& next){
      child->execute(prev,action,next);
    }

    virtual void update() {
      child->update();
      value=child->get_value();
      value.first=value.second-value.first;
    }

    unit_tag* child;

  };

  class unit_tagleaf: public unit_tag {
  public:
    unit_tagleaf(int tag):my_tag(tag) {
      value.first=0;
      value.second=1;
    }

    virtual ~unit_tagleaf() {
    }

    virtual void set_instance(int instance,int current_instance, bool force=false) {
      if (force) {
	leaf_instance_map[current_instance]=value.first;
	value.first=leaf_instance_map[instance];
      }
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
    
    virtual void execute(const std::vector<int>& prev,int action,const std::vector<int>& next){

      if (value.first<value.second &&
	  ((left_side  && std::find(prev.begin(), prev.end(), my_tag)!=prev.end()) ||
	   (!left_side && std::find(next.begin(), next.end(), my_tag)!=next.end()))) {
	value.first++;
      }
    }
    
  protected:
    int my_tag;
    std::stack<val> st;
    std::map<int,int> leaf_instance_map;
  };

  class unit_leaf: public unit {
  public:
    unit_leaf(int action, int count=1) : my_action(action)
    {
      value.second=count;
    }

    virtual void set_instance(int instance,int current_instance, bool force=false) {
      if (force) {
	leaf_instance_map[current_instance]=value.first;
	value.first=leaf_instance_map[instance];
      }
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

    virtual void execute(const std::vector<int>& prev,int action,const std::vector<int>& next) {
      if (action==my_action && value.first<value.second)
          value.first++;
    }

    virtual void update() {
    }

  protected:
    int my_action;
    std::stack<val> st;
    std::map<int,int> leaf_instance_map;
  };

  class unit_tagdual : public unit_tag {
  public:
    unit_tagdual(unit_tag*l,unit_tag*r): left(l),right(r) {
    }

    virtual void set_instance(int instance,int current_instance, bool force=false) {
      left->set_instance(instance,current_instance,force);
      right->set_instance(instance,current_instance,force);
    }

    virtual void set_left(bool l) {
      unit_tag::set_left(l);
      left->set_left(l);
      right->set_left(l);
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

    /*
    virtual void execute(const std::vector<int>& prev,int action,const std::vector<int>& next) {
      val v(right->get_value());

      if (v.first==v.second) {
	left->execute(prev,action,next);
      } else {
	right->execute(prev,action,next);
	right->update();
	v=right->get_value();
	if (v.first==v.second) {
	  left->execute(prev,action,next);
	}
      }
    }
    */
    virtual void update() {
      right->update();
      left->update();
    }

    virtual ~unit_tagdual() {
      delete left;
      delete right;
    }

    unit_tag* left;
    unit_tag* right;
  };

  class unit_tagunit: public unit_tagdual {
  public:
    unit_tagunit(unit_tag* l, unit* _child,unit_tag* r): unit_tagdual(l,r),child(_child) {
      value.first=0;
      value.second=l->value.second+right->value.second+child->value.second;      
    }

    virtual ~unit_tagunit() {
      delete child;
    }

    virtual void set_instance(int instance,int current_instance, bool force=false) {
      unit_tagdual::set_instance(instance,current_instance,force);
      child->set_instance(instance,current_instance,force);
    }

    virtual void execute(const std::vector<int>& prev,int action,const std::vector<int>& next) {
      /*
	ööh. ei noin. vaan näin?

	if (!left) {
	  execute(left);
	  if (!left) {
	    return;
	  }
	}
	if (!child) {
	  execute(child);
	  if (!child) {
	    return;
	  }
	}
	if (!right) {
	  execite(right);
	  if (!right) {
	    return;
	  }
	}
       */

      left->update();
      val v=left->get_value();
      if (v.first<v.second) {
	left->execute(prev,action,next);
	left->update();
	v=left->get_value();
	if (v.first<v.second) {
	  return;
	}
      }

      child->update();
      v=child->get_value();
      if (v.first<v.second) {
	child->push();
	child->execute(prev,action,next);
	child->update();
	v=child->get_value();
	child->pop();
	if (v.first<v.second) {
	  if (v.first==0) {
	    // Handle nothing has happened case, when we need left side to be filled
	    // when starting executing the child.
	    // btw... we won't execute anyting on the right side before the action part
	    // is covered.
	    left->reset();
	  } else {
	    // something happened. We aren't at the goal yet, but on the way!
	    // So this is something that we want to include
	    child->execute(prev,action,next);
	  }
	  return;
	} else {
	  // We are on the way to the goal!
	  // Let's check if this is allowed goal

	  right->execute(prev,action,next);	  
	  right->update();
	  v=right->get_value();
	  if (v.first==v.second) {
	    // GOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOAL
	    child->execute(prev,action,next);
	    return;
	  } else {
	    // No goal.
	    right->reset();
	  }
	}
      }


    }  
    

    virtual void reset() {
      unit_tagdual::reset();
      child->reset();
    }
    
    virtual void update() {
      unit_tagdual::update();
      child->update();
      value.second=left->value.second+
	right->value.second+
	child->value.second;

      value.first=left->value.first+
	right->value.first+
	child->value.first;
    }      
    
    virtual void push() {
      unit_tagdual::push();
      child->push();
    }

    virtual void pop() {
      unit_tagdual::pop();
      child->pop();
    }
    
    unit* child;
  };

  class unit_tagand : public unit_tagdual {
  public:
    unit_tagand(unit_tag* l,unit_tag*r): unit_tagdual(l,r) {
      value.second=l->value.second+right->value.second;
    }
    virtual ~unit_tagand() {}

    virtual void execute(const std::vector<int>& prev,int action,const std::vector<int>& next) {
      left->execute(prev,action,next);
      right->execute(prev,action,next);
    }

    virtual void update() {
      unit_tagdual::update();
      value.first=left->value.first+right->value.first;
    }
  };

  class unit_tagor : public unit_tagdual {
  public:
    unit_tagor(unit_tag* l,unit_tag*r): unit_tagdual(l,r) {
      value.second=left->value.second+right->value.second;
    }
    virtual ~unit_tagor() {}

    virtual void execute(const std::vector<int>& prev,int action,const std::vector<int>& next) {
      left->execute(prev,action,next);
      right->execute(prev,action,next);
    }
    
    virtual void update() {
      unit_tagdual::update();
      if (left->value.first==left->value.second ||
	  right->value.first==right->value.second) {
	value.first=left->value.second+right->value.second;
      } else {
	value.first=left->value.first+right->value.first;
      } 
    }
  };


  class unit_mult: public unit {
  public:
    unit_mult(unit* l,int i): max(i),child(l),count(0) {
    }

    virtual void set_instance(int instance,int current_instance, bool force=false) {
      instance_map[current_instance]=count;
      count=instance_map[instance];
      child->set_instance(instance,current_instance,force);
    }

    virtual void reset() {
      count=0;
      child->reset();
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

    virtual void execute(const std::vector<int>& prev,int action,const std::vector<int>& next) {
      update();
      if (count<max)
	child->execute(prev,action,next);
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
    std::map<int,int > instance_map;
  };

protected:
  std::vector<unit*> Units;
  std::string params;
};


#endif
