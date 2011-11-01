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
#ifndef __heuristic_hh__
#define __heuristic_hh__

#include <vector>
#include <string>

#include "factory.hh"

class Coverage;
class Model;
class Log;

class Heuristic {
public:
  Heuristic(Log& l, std::string params = "");

  virtual bool execute(int action);
  std::vector<std::string>& getAllActions();

  virtual float getCoverage();
  virtual int getAction()=0;
  virtual int getIAction()=0;

  std::string& getActionName(int action);
  Model* get_model();

  void set_coverage(Coverage* c);
  void set_model(Model* _model);

protected:
  std::vector<Coverage*> coverage;
  Model* model;
  Coverage* my_coverage;
  std::string none;
  Log& log;
};

FACTORY_DECLARATION(Heuristic);

#endif
