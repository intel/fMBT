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
#ifndef __adapter_h__
#define __adapter_h__

#include <vector>
#include <string>
#include <map>
#include "writable.hh"
#include "helper.hh"
#include "factory.hh"
#include "log.hh"

/* Creating and initialising an adapter is a call sequence

   1. constructor(log, params) where params contain configuration
   arguments

   2. set_actions(actions), by default just stored to the "actions"
   member.

   3. init()

   If is ready for responding to execute() and observe(), init()
   returns true. If init() returns false, stringify() may return
   reason for failure.
*/

class Adapter: public Writable {
public:
  Adapter(Log& l, std::string params = "");
  virtual void set_actions(std::vector<std::string>* _actions);
  virtual bool init();

  /** \brief execute an action and report results
   * \param action input/output parameter for suggesting and reporting
   *               executed action
   *
   * When called, action table contains exactly one action: executing
   * action[0] is suggested by the test generator. At exit it contains
   * the action whose execution is reported. Reporting more unusual
   * cases:
   *
   * 1. Result of the execution does not match any of the known
   *    actions: action table contains only integer 0.
   *
   * 2. Execution result corresponds to more than one actions:
   *    action table contains all alternative actions.
   *
   * 3. Execution of the suggested action is blocked:
   *    action table is empty.
   */
  virtual void execute(std::vector<int> &action) = 0;

  /** \brief report observed events
   * \param action (output) corresponds to observed event
   * \param block should adapter wait for events
   * \return true if events have been observed
   *
   * observe reports one event at a time. If an event matches to
   * multiple actions, all alternative actions are returned in the
   * action parameter.
   *
   * If block is false, observe should report events occured so
   * far. Otherwise it should wait for events and return either when
   * there is something to report or when there will not be anything
   * to report.
   */
  virtual bool observe(std::vector<int> &action, bool block = false) = 0;

  /* Adapter stack / tree setup and browsing API */
  void setparent(Adapter* a);
  virtual Adapter* up();
  virtual Adapter* down(unsigned int a);
  virtual std::vector<std::string>& getAdapterNames();

  /* Methods for reading action names */
  virtual std::vector<std::string>& getAllActions();

  /// Returns action name for string comparisons
  std::string getActionName(int action);

  /// Returns escaped action name (can be logged to XML)
  const char* getUActionName(int action);

protected:
  Log& log;
  std::vector<std::string>* actions;

  std::vector<const char*> unames;
  Adapter* parent;
  std::vector<std::string> adapter_names;
};

FACTORY_DECLARATION(Adapter);

#endif
