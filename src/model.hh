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
#ifndef __model_hh__
#define __model_hh__

#include <vector>
#include <string>
#include <map>
#include "helper.hh"
#include "log.hh"
#include "writable.hh"

#define SILENCE      (-3)
#define DEADLOCK     (-2)
#define OUTPUT_ONLY  (-1)

class Model;
class Writable;

class Model: public Writable {
public:
  Model(Log&l):log(l), parent(NULL) {}
  typedef Model*(*creator)(Log&);

  static void add_factory(std::string name, creator c);
  static Model* create(Log&,std::string name);

  //! Returns names of all actions available
  std::vector<std::string>& getActionNames() {
    return action_names;
  }

  //! Returns the name of the given action
  std::string& getActionName(int action) {
    return action_names[action];
  }

  /*! 
   * Returns the number of actions executable in the current state.
   * The (out) parameter refers to the array containing the actions.
   */
  virtual int getActions(int** actions) =0;

  /*!
   * Returns the number of input actions executable in the current state.
   * The (out) parameter refers to the array containing the actions.
   */
  virtual int getIActions(int** actions)=0;

  //! Reset the current state to the initial state. Returns false if not possible.
  virtual bool reset()                  =0;

  //! Execute the given action in the current state. Returns false if not possible.
  virtual int  execute(int action)      =0;

  //! Push the current state of the model to the stack
  virtual void push() =0;

  //! Pop a state from the stack and set it as a current state
  virtual void pop() =0;

  /* Let's hope this won't be called too often with large 
   * number of outputs/inputs..
   */
  bool is_output(int action)
  {
    if (outputs.size()<inputs.size()) {
      for(size_t i=0;i<outputs.size();i++) {
	if (outputs[i]==action) {
	  return true;
	}
      }
      return false;
    }
    
    for(size_t i=0;i<inputs.size();i++) {
      if (inputs[i]==action) {
	return false;
      }
    }
    
    return true;
  }

  /*!
   * Loads model based on the given name.
   * Returns false if loading failed.
   */
  virtual bool load(std::string& name)  =0;


  void precalc_input_output()
  {
    for(size_t i=0;i<action_names.size();i++) {
      if (isOutputName(action_names[i])) {
	outputs.push_back(i);
      }
      
      if (isInputName(action_names[i])) {
	inputs.push_back(i);
      }
    }
  }

  virtual int action_number(std::string& s) {
    for(size_t i=0;i<action_names.size();i++) {
      if (action_names[i]==s) {
	return i;
      }
    }
    return -1;
  }

  virtual Model* up() { return parent; }
  virtual Model* down(unsigned int a) { return NULL; }
  virtual std::vector<std::string>& getModelNames() { return model_names; }

  void setparent(Model* m) { parent = m; }

private:
  static std::map<std::string,creator>* factory;
protected:
  Log &log;
  std::vector<std::string> action_names; /* action names.. */
  std::vector<int> inputs;  /* all input action numbers */
  std::vector<int> outputs; /* all output action numbers */
  Model* parent;
  std::vector<std::string> model_names;
};

namespace {
  class model_factory {
  public:
    model_factory(std::string name, Model::creator c) {
      Model::add_factory(name,c);
    }
  };
};
#endif

