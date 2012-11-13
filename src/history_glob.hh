/*
 * fMBT, free Model Based Testing tool
 * Copyright (c) 2012, Intel Corporation.
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
#ifndef __history_glob_hh__
#define __history_glob_hh__

#include "history.hh"
#include "alphabet.hh"
#include <vector>
#include <glob.h>

class History_glob: public History {
public:
  History_glob(Log& l, std::string _params = "");
  virtual ~History_glob() {
    globfree(&gl);
  }
  virtual Alphabet* set_coverage(Coverage*,Alphabet* alpha);

protected:
  glob_t gl;
  std::string params;
};

#endif
