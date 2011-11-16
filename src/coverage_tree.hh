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

class Coverage_Tree: public Coverage {

public:
  Coverage_Tree(Log& l, std::string params);
  virtual void push();
  virtual void pop();

  virtual bool execute(int action);
  virtual float getCoverage();

  virtual int fitness(int* actions,int n, float* fitness);

  void set_max_depth(std::string&s);

  virtual void set_model(Model* _model);

protected:
  void precalc();
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
  std::list<std::list<std::pair<struct node*, int> > > push_restore;

  struct node root_node;
  long node_count;
  long max_count;

  std::map<int,struct node*> exec;

  void print_tree(struct node* node,int depth);

};

#endif

