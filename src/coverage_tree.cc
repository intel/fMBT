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
#include "coverage_tree.hh"
#include "model.hh"
#include <cstdlib>
#include "helper.hh"

std::vector<Coverage_Tree::node*> Coverage_Tree::nodes_save;

Coverage_Tree::Coverage_Tree(Log& l,const std::string& _params) :
  Coverage(l), max_depth(2), push_depth(0),have_filter(false), params(_params)
{
  commalist(params,subs);
  set_max_depth(subs[0]);

  set_instance(0);
  (*exec)[0].first = &root_node;

  push();

  if ((subs.size()>1) && (((unsigned)max_depth+1)!=subs.size())) {
    status=false;
    errormsg="incorrect number of params. Expecting "+to_string(max_depth+1);
  }
  if (subs.size()>1) {
    have_filter=true;
  }
}

bool Coverage_Tree::set_instance(int instance)
{
  if (instance_map.find(instance)==instance_map.end()) {
    instance_map[instance] = new_exec();
  }
  exec=instance_map[instance];
  // Can do this, because push-depth requirements when changing instance
  prev_exec=exec;
  return true;
}

void Coverage_Tree::push()
{
  push_depth++;
  std::list<std::pair<struct node*, int> > a;
  push_restore.push(a);
  exec_restore.push(
		    std::pair<
		      std::vector<std::pair<struct node*,bool> >*,
		      std::vector<std::pair<struct node*,bool> >*
		      >
		    (exec,prev_exec));
  // handle push push case
  if (!((*exec)[0].first)) 
    prev_exec=exec;

  exec = new_exec();
  node_count_restore.push_back(node_count);
}

void Coverage_Tree::pop()
{
  std::list<std::pair<struct node*, int> >::iterator i
    = push_restore.top().begin();

  std::list<std::pair<struct node*, int> >::iterator e
    = push_restore.top().end();

  while(i!=e) {
    int action=i->second;
    struct node* current_node=i->first;
    delete_node(current_node->nodes[action]);
    current_node->nodes[action]=NULL;
    current_node->nodes.erase(action);
    ++i;
  }
  push_restore.pop();

  delete_exec(exec);

  exec=exec_restore.top().first;
  prev_exec=exec_restore.top().second;

  exec_restore.pop();

  node_count=node_count_restore.back();
  node_count_restore.pop_back();

  push_depth--;
}

void Coverage_Tree::precalc()
{
  if (model) {
    if (have_filter) {
      strlist(subs);
      std::vector<std::string> &model_action_names=model->getActionNames();
      // We have a filter!
      for(int i=0;i<max_depth;i++) {
	std::string& filt=subs[i+1];
	std::vector<int> result;
        regexpmatch(filt,model_action_names,result,false,1,1);
	if (result.empty()) {
	  status=false;
	  errormsg="No match for regexp "+filt;
	}
	act_depth.push_back(result.size());
	for(unsigned j=0;j<result.size();j++) {
	  mask[std::pair<int,int>(i,result[j])]=true;
	}
      }
    }

    node_count=1;
    max_count=0;
    long ccount=1;
    for(int i=0;i<max_depth;i++) {
      ccount*=actions_at_depth(i);
      max_count+=ccount;
    }
  }
}

int Coverage_Tree::actions_at_depth(int depth) {
  if (!have_filter) {
    static int retval=model->getActionNames().size()-1;
    return retval;
  }
  return act_depth[depth];
}

inline bool Coverage_Tree::filter(int depth,int action)
{
  if (!have_filter) {
    return true;
  }
  return mask[std::pair<int,int>(depth,action)];
}

void Coverage_Tree::set_model(Model* _model)
{
  Coverage::set_model(_model);
  precalc();
}

void Coverage_Tree::history(int action,std::vector<int>& props,
			    Verdict::Verdict verdict)
{
  if (action) {
    execute(action);
  } else {
    // verdict. And now we should do ??
    (*exec).clear();
    (*exec).resize(max_depth+1);
    (*exec)[0].first = &root_node;
    prev_exec=exec;
  }
}

Coverage_Tree::~Coverage_Tree()
{
  if (push_depth) {
    pop();
  } else {
    abort();
  }

  for(std::map<int,std::vector<std::pair<struct node*,bool> >*>::iterator i=
	instance_map.begin();i!=instance_map.end();++i) {
    delete i->second;
  }

  for(;!exec_save.empty();exec_save.pop_back()) {
    delete exec_save.back();
  }

}

bool Coverage_Tree::execute(int action)
{
  struct node* current_node=&root_node;
  struct node* next_node;
  int depth=0;
  bool _filt=true;
  while (depth<max_depth) {
    bool filt=filter(depth,action);
    _filt&=filt;
    if (_filt && current_node->nodes.find(action)==current_node->nodes.end()) {
      current_node->nodes[action]=new_node(action);//new struct node;

      node_count++;
      if (push_depth) {
	push_restore.top().push_front(std::pair<struct node*, int>
				      (current_node,action));
      }
    }
    depth++;
    next_node=(*prev_exec)[depth].first;
    bool _filt_tmp=(*prev_exec)[depth].second;
    if (current_node) {
      (*exec)[depth]=std::pair<struct node*, bool>(current_node->nodes[action],_filt);
    } else {
      (*exec)[depth]=std::pair<struct node*, bool>(NULL,_filt);
    }
    _filt=_filt_tmp;
    current_node=next_node;
  }
  prev_exec=exec;

  return true;
}


float Coverage_Tree::getCoverage()
{
  return (float)(node_count-1)/max_count;
}

void Coverage_Tree::print_tree(struct node* node,int depth)
{
  for(int j=0;j<32;j++) {
    if (node->nodes[j]) {
      for(int i=0;i<depth;i++) {
	log.debug("|");
      }
      log.debug("%s\n",model->getActionName(node->nodes[j]->action).c_str());
      print_tree(node->nodes[j],depth+1);
    }
  }
}

int Coverage_Tree::fitness(int* action,int n,float* fitness)
{
  int ret=0;

  if (log.is_debug()) {
    log.debug("Tree\n");
    print_tree(&root_node,0);
  }

  for(int pos=0;pos<n;pos++) {
    float f=0;
    struct node* no=(*exec)[0].first;
    for(int i=0;(i<max_depth)&& no;i++) {
      if (no->nodes[action[pos]]==NULL) {
	f+=1.0/(i+1.0);
      }
      no=(*exec)[i+1].first;
    }
    fitness[pos]=f;
    if (fitness[pos]>fitness[ret]) {
      ret=pos;
    }
  }

  return ret;
}

void Coverage_Tree::set_max_depth(std::string&s)
{
  if (s!="") {
    max_depth=std::atoi(s.c_str());
    if (max_depth<1) {
      max_depth=1;
    }
  }
  precalc();
  log.debug("%s(%s) -> %i\n",__PRETTY_FUNCTION__,s.c_str(),max_depth);
}

FACTORY_DEFAULT_CREATOR(Coverage, Coverage_Tree, "perm")
