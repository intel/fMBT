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

class Coverage_Tree: public Coverage {

public:
  Coverage_Tree(Log& l, std::string params);
  virtual void push(){};
  virtual void pop(){};

  virtual bool execute(int action);
  virtual float getCoverage();

  virtual int fitness(int* actions,int n, float* fitness);

  void set_max_depth(std::string&s);

  virtual void set_model(Model* _model);

protected:
  void precalc();
  int max_depth;

  struct node;

  struct node {
    int action;
    std::map<int,struct node*> nodes;
  };

  struct node root_node;
  long node_count;
  long max_count;

  std::map<int,struct node*> exec;

  void print_tree(struct node* node,int depth);

};

#endif

