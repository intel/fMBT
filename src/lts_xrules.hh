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
#ifndef __lst_xrules_hh__
#define __lst_xrules_hh__

#include "model.hh"
#include <map>

class Lts_xrules : public Model {
public:
  Lts_xrules(Log&l): Model(l) {}
  virtual bool reset();
  virtual int  execute(int action);

  virtual int getprops(int** props);

  virtual void push();
  virtual void pop();

  virtual int getActions(int** actions); // vireessä olevat tapahtumat
  virtual int getIActions(int** actions); // Vireessä olevat syöte tapahtumat. NULL ja 0 == DEADLOCK.

  virtual bool load(std::string& name);

  void add_file(unsigned int index,std::string& filename);
  void add_result_action(std::string* name);
  void add_component(unsigned int index,std::string& name);
  void print_root_par();
  virtual std::string stringify();

  virtual Model* down(unsigned int a) {
    if (a>=lts.size()) {
      return NULL;
    }
    return lts[a];
  }
  
protected:
  void compose();
  void prop_create();

  std::vector<int> pzero;
  std::vector<int> tprops;
  
  /* type, which contains component number (1 = "general_camera.lsts") 
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
  void print_par(std::ostringstream& t,std::string name,
		 struct par* pa);
  /* Replaced by model_names 
     std::vector<std::string> lts_filenames;
  */
  std::vector<Model*> lts;

  /* Root structure */
  struct par root_par;
  /* current sturcture. Used when loading .xrules */
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
  std::vector<struct par*> res_nodes;

  /* Api compatibility */
  int* _res_actions;
  int* _res_iactions;
};

#endif
