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
#include "log.hh"
#include "writable.hh"
#include "factory.hh"

#define SILENCE      (-3)
#define DEADLOCK     (-2)
#define OUTPUT_ONLY  (-1)

class Model;
class Writable;

class Model: public Writable {
public:
  Model(Log&l, std::string params = "");

  //! Returns names of all actions available.
  std::vector<std::string>& getActionNames();

  //! Returns names of all available state propositions
  std::vector<std::string>& getSPNames();

  //! Returns the name of the given action
  std::string& getActionName(int action);

  /*! 
   * Returns the number of actions executable in the current state.
   * The (out) parameter refers to the array containing the actions.
   * Data might become invalid/corrupted after executing an action
   */
  virtual int getActions(int** actions) =0;

  /*!
   * Returns the number of input actions executable in the current state.
   * The (out) parameter refers to the array containing the actions.
   * Data might become invalid/corrupted after executing an action
   */
  virtual int getIActions(int** actions)=0;

  //! Reset the current state to the initial state. Returns false if not possible.
  virtual bool reset()                  =0;

  //! Execute the given action in the current state. Returns false if not possible.
  virtual int  execute(int action)      =0;

  /*!
   * Returns the number of state propositions at current state
   * The (out) parameters refers to the array containing the propositions.
   */
  virtual int getprops(int** props)     =0;

  //! Push the current state of the model to the stack
  virtual void push()                   =0;

  //! Pop a state from the stack and set it as a current state
  virtual void pop()                    =0;

  /* Let's hope this won't be called too often with large 
   * number of outputs/inputs..
   */
  bool is_output(int action);

  /*!
   * Loads model based on the given name.
   * Returns false if loading failed.
   */
  virtual bool load(std::string& name)  =0;

  void precalc_input_output();

  virtual int action_number(std::string& s);

  virtual Model* up();
  virtual Model* down(unsigned int a);
  virtual std::vector<std::string>& getModelNames();

  void setparent(Model* m);

protected:
  Log &log;
  std::vector<std::string> prop_names; /* proposition names.. */
  std::vector<std::string> action_names; /* action names.. */
  std::vector<int> inputs;  /* all input action numbers */
  std::vector<int> outputs; /* all output action numbers */
  Model* parent;
  std::vector<std::string> model_names;
};

FACTORY_DECLARATION(Model)

#endif

