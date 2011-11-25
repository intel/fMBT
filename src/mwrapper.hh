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

#ifndef __mwrapper_hh__
#define __mwrapper_hh__

#include <vector>
#include <string>
#include <fstream>

#include "model.hh"
#include "log.hh"
#include "aal.hh"

#define SILENCE      (-3)
#define DEADLOCK     (-2)
#define OUTPUT_ONLY  (-1)

class Mwrapper: public Model {
public:
  Mwrapper(Log&l, std::string params, aal* _model):
    Model(l, params), model(_model)  {}

  virtual int getActions(int** actions); // vireessä olevat tapahtumat
  virtual int getIActions(int** actions); // Vireessä olevat syöte tapahtumat. NULL ja 0 == DEADLOCK.
  // NULL ja 1 == OUTPUTONLY
  virtual bool reset();
  virtual int getprops(int** props);
  virtual int  execute(int action);
  virtual void push();
  virtual void pop();

  virtual bool load(std::string& name);

  virtual std::string stringify();

protected:
  aal* model;
};

#endif

