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
#ifndef __history_hh__
#define __history_hh__

#include <vector>
#include <string>

#include "factory.hh"
#include "writable.hh"
#include "coverage.hh"
#include "alphabet.hh"
#include <sys/time.h>

class Log;

class History: public Writable {
public:
  History(Log& l, std::string params = "") : model_getactions(false),model_execute(false),adapter_execute(false),tag_getprops(false),tag_checktags(false),coverage_execute(true),log(l) {test_verdict="N/A";log.ref();}
  virtual ~History() {log.unref();};

  virtual Alphabet* set_coverage(Coverage*,Alphabet* alpha) =0;

  static struct timeval current_time;
  std::string test_verdict;
protected:
  bool model_getactions;
  bool model_execute;
  bool adapter_execute;
  bool tag_getprops;
  bool tag_checktags;

  bool coverage_execute;

  Log& log;
};

FACTORY_DECLARATION(History)

History* new_history(Log&, std::string&);

#endif
