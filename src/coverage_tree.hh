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

/* Coverage_Tree implements a permutation coverage. Coverage reaches
 * 1.0 when all permutations of any n subsequent actions have been
 * executed. n is given as a parameter.
 */

#ifndef __coverage_tree_hh__
#define __coverage_tree_hh__

#include "coverage.hh"

#include <map>
#include <list>
#include <stack>

class Coverage_Tree: public Coverage {

public:
  Coverage_Tree(Log& l,const std::string& _params);
  virtual ~Coverage_Tree();
  virtual void push();
  virtual void pop();

  virtual void history(int action, std::vector<int>& props, 
		       Verdict::Verdict verdict);
  virtual bool execute(int action);
  virtual float getCoverage();

  virtual int fitness(int* actions,int n, float* fitness);

  void set_max_depth(std::string&s);

  virtual void set_model(Model* _model);

  virtual bool set_instance(int instance);

protected:
  void precalc();
  bool filter(int depth,int action);
  int max_depth;

  /* 
     The data structure

     root_node is the root of the tree where each node represents an
     executed action, and contains a map of actions executed after it.

     exec points to nodes that need to be updated on next execute().
     
     Example how data structure evolves when two actions are executed
     with depth == 3:
     
     0. Initial state:
     
        exec = {0 -> root_node}
     
        root_node
          .action = 0
          .nodes = {}
     
     1. Add action 42:
     
        exec = {0 -> root_node,
                1 -> node_1}

        root_node
          .action = 0
          .nodes = {42 -> node_1}

        node_1
          .action = 42
          .nodes = {}

    2. Add action 53:

       exec = {0 -> root_node,
               1 -> node_2,
               2 -> node_1}

       root_node
         .action = 0
         .nodes = {42 -> node_1,
                   53 -> node_2}

       node_1
         .action = 42
         .nodes = {53 -> node_3}

       node_2
         .action = 53
         .nodes = {}

       node_3
         .action = 53
         .nodes = {}
   */


  struct node;

  struct node {
    int action;
    std::map<int,struct node*> nodes;
  };

  int push_depth;
  std::stack<std::list<std::pair<struct node*, int> > > push_restore;
  std::stack<std::pair<std::vector<std::pair<struct node*,bool> >*, std::vector<std::pair<struct node*,bool> >* > > exec_restore;
  std::vector<long > node_count_restore;

  struct node root_node;
public:
  long node_count;
  long max_count;
protected:
  inline std::vector<std::pair<struct node*,bool> >* new_exec() {
    std::vector<std::pair<struct node*,bool> >* ret;

    if (exec_save.empty()) {
      ret = new std::vector<std::pair<struct node*,bool> >(max_depth+1);
    } else {
      ret = exec_save.back();
      exec_save.pop_back();
    }
    return ret;
  }

  inline void delete_exec(std::vector<std::pair<struct node*,bool> >* n) {
    exec_save.push_back(n);
    (*n)[0].first=NULL;
  }

  static inline struct node* new_node(int action) {
    struct node* ret;

    if (nodes_save.empty()) {
      ret = new struct node;
    } else {
      ret=nodes_save.back();
      nodes_save.pop_back();
    }

    ret->action=action;
    return ret;
  }

  static inline void delete_node(struct node* n) {
    nodes_save.push_back(n);
    n->nodes.clear();
  }
  static std::vector<struct node*> nodes_save;
  std::vector<std::vector<std::pair<struct node*,bool> >*> exec_save;

  bool have_filter;
  std::string params;
  std::vector<std::string> subs;
  std::vector<std::pair<struct node*,bool> >* exec;
  // To avoid extra copying....
  std::vector<std::pair<struct node*,bool> >* prev_exec;

  std::map<std::pair<int,int>, bool> mask;
  std::vector<int> act_depth;

  void print_tree(struct node* node,int depth);
  int actions_at_depth(int depth);

  std::map<int,std::vector<std::pair<struct node*,bool> >*> instance_map;

};

#endif

