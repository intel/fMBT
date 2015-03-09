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

#ifndef __reffable_hh__
#define __reffable_hh__

class reffable {
public:
  reffable(void** _nullme=NULL): refcount(0),nullme(_nullme) {}
  virtual ~reffable() {}

  void ref() {
    refcount++;
  }

  void unref() {
    refcount--;
    if (refcount<=0) {
      if (nullme) {
	*nullme=NULL;
      }
      delete this;
    }
  }
protected:
  int refcount;
  void** nullme;
};

#endif
