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
#ifndef __adapter_xrules_hh__
#define __adapter_xrules_hh__

#include "adapter.hh"
#include "model.hh"
#include <map>

class Adapter_xrules : public Adapter, public Model {
public:
  Adapter_xrules(std::vector<std::string>& _actions) : Adapter(_actions) {
    action_names=_actions;
  }
  virtual int execute(int action);
  virtual bool observe(int &action,bool block=false);  

  bool load(std::string& name);

  void add_file(unsigned index,std::string& filename, std::string& adaptername);
  void add_result_action(std::string* name);
  void add_component(int index,std::string& name);

  virtual int getActions(int**);
  virtual int getIActions(int**);


protected:
  bool reset(); // Interlanl...

  void compose();
  
  /* type, which contains component number (1 = "general_camera.lsts" , "v4l2") 
   * and action number (within the component)
   * So comp(1,2) refers to action number 2 in the component 1.
   */
  typedef std::pair<int, int> comp;

  /*
   * The structure.
   *
   * parent: for root node NULL
   * actions: result actions for the node.
   * vmap: maps <component, action> to next node.
   * count: last update count
   * added_count: previous time the node was active
   * active_next: list for active nodes.
   * me: <component, action>. Information about the node.
   * parent->vmap[this.me] points to this
   *
   */

  struct par {
    par() { count=0;added_count=0;root_count=NULL; };
    par(struct par* p) { 
      parent = p;
      root_count = p->root_count;
      count=0;
      added_count=0;
      root_count=NULL;
    };
    struct par* parent;
    std::vector<int> actions;
    std::map<comp, struct par*> vmap;

    /* for parallel composition structure cleanup */
    unsigned count;
    unsigned* root_count;
    unsigned added_count;
    struct par* active_next;
    comp me;
  };

  /* Bob maps <component,action> to the sturcture */

  std::multimap<comp,struct par*> bob;

  /* */
  bool parent_active_par(struct par* par);

  /* debug print.. */
  void print_par(struct par* pa);
  void print_root_par();

  std::vector<std::string> adapter_filenames;
  std::vector<std::string> lts_filenames;
  std::vector<Model*> lts;
  std::vector<Adapter*> adapters;

  /* Root structure */
  struct par root_par;
  /* current sturcture. Used when loading .xrules_e */
  struct par* cur_par;
  
  /* head of the active list */
  struct par* active_root;
  
  /* Do we need to compose or not */
  int valid;

  /* Result actions, if valid */
  std::vector<int> res_actions;
  /* Result input actions, if valid */
  std::vector<int> res_iactions;
  /* pointers to THE structure. Accessed by result action.
   * Note. We support only deterministic results.
   */
  std::multimap<int,struct par*> res_nodes;

  /* Api compatibility */
  int* _res_actions;
  int* _res_iactions;

};

#endif
