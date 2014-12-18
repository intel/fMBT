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

#ifndef __RANDOM_HH__
#define __RANDOM_HH__

#ifdef FACTORY_CREATOR_PARAMS

#undef FACTORY_CREATOR_PARAMS
#undef FACTORY_CREATOR_PARAMS2
#undef FACTORY_CREATE_PARAMS

#endif  /*  FACTORY_CREATOR_PARAMS  */


#define FACTORY_CREATOR_PARAMS std::string params
#define FACTORY_CREATOR_PARAMS2 params
#define FACTORY_CREATE_PARAMS                                          \
                       std::string name,                               \
                       std::string params

#include "factory.hh"
#include "writable.hh"
#include "reffable.hh"

class Random;
class Random: public Writable, public reffable {
public:
  Random(): single(false) {}
  virtual ~Random() {}
  virtual unsigned long rand() = 0;
  virtual double drand48() {
    return (1.0*rand()) / (1.0*max_val+1.0);
  }
  unsigned long max_val;
  static Random* _default_random;
  static Random* default_random();
  bool single;
};

FACTORY_DECLARATION(Random)

Random* new_random(const std::string&);

#ifndef _RANDOM_INTERNAL_

#undef FACTORY_CREATOR_PARAMS
#undef FACTORY_CREATOR_PARAMS2
#undef FACTORY_CREATE_PARAMS

#define FACTORY_CREATE_PARAMS Log& log,                                \
                       std::string name,                               \
                       std::string params
#define FACTORY_CREATOR_PARAMS Log& log, std::string params
#define FACTORY_CREATOR_PARAMS2 log, params

#endif /*  _RANDOM_INTERNAL_ */

#endif /* __RANDOM_HH__ */
