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

#ifndef __end_condition_hh__
#define __end_condition_hh__

#include "verdict.hh"
#include "writable.hh"
#include <string>

struct End_condition: public Writable {

  typedef enum {
    STEPS = 0,
    COVERAGE,
    STATETAG,
    DURATION,
    NOPROGRESS
  } Counter;

  End_condition(Verdict::Verdict v, Counter c, std::string* p);
  ~End_condition();

  Verdict::Verdict verdict;
  Counter counter;
  std::string* param;

  float param_float;
  long param_long;
  time_t param_time;

};

#endif
