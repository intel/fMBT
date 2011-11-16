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

Coverage_Tree::Coverage_Tree(Log& l, std::string params) :
  Coverage(l), max_depth(2)
{ 
  exec[0] = &root_node;
  set_max_depth(params);
}

void Coverage_Tree::push()
{
  push_depth++;
  std::list<std::pair<struct node*, int> > a;
  push_restore.push_front(a);
}

void Coverage_Tree::pop()
{
  std::list<std::pair<struct node*, int> >::iterator i
    = push_restore.front().begin();

  while(i!=push_restore.front().end()) {
    node_count--;
    int action=i->second;
    struct node* current_node=i->first;
    delete current_node->nodes[action];
    current_node->nodes[action]=NULL;
    current_node->nodes.erase(action);
    i++;
  }
  
  push_restore.pop_front();
  push_depth--;
}
void Coverage_Tree::precalc()
{
  if (model) {
    node_count=1;
    max_count=0;
    int acount=model->getActionNames().size();
    long ccount=acount;
    for(int i=1;i<=max_depth;i++) {
      max_count+=ccount;
      ccount*=acount;
    }
  }
}

void Coverage_Tree::set_model(Model* _model)
{
  Coverage::set_model(_model);
  precalc();
}


bool Coverage_Tree::execute(int action)
{
  struct node* current_node=&root_node;
  struct node* next_node;
  int depth=0;
  while (current_node && depth<max_depth) {
    if (current_node->nodes[action]==NULL) {
      current_node->nodes[action]=new struct node;
      current_node->nodes[action]->action=action;
      node_count++;
      if (push_depth) {
	std::pair<struct node*, int> a(current_node,action);
	push_restore.front().push_front(a);
      }
    }
    depth++;
    next_node=exec[depth];
    exec[depth]=current_node->nodes[action];
    current_node=next_node;
  }

  return true;
}


float Coverage_Tree::getCoverage()
{
  return (float)node_count/max_count;
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

  log.debug("Tree\n");

  print_tree(&root_node,0);

  for(int pos=0;pos<n;pos++) {
    float f=0;
    struct node* no=exec[0];
    for(int i=0;(i<max_depth)&& no;i++) {
      if (no->nodes[action[pos]]==NULL) {
	f+=1.0/(i+1.0);
      }
      no=exec[i+1];
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

FACTORY_DEFAULT_CREATOR(Coverage, Coverage_Tree, "perm");
