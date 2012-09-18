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
#ifndef __history_log_hh__
#define __history_log_hh__

#include "history.hh"
#include "alphabet.hh"
#include <libxml/xmlreader.h>

#include "alphabet_impl.hh"

class History_log: public History {
public:
  History_log(Log& l, std::string params = "");
  virtual ~History_log() {};
  virtual void set_coverage(Coverage*,Alphabet* alpha);

protected:
  int alphabet_done;
  char* act;
  char* tag;
  void processNode(xmlTextReaderPtr reader);
  Coverage* c;
public:
  Alphabet* a;
private:
  void send_action();
  bool send_action(std::string& a,std::vector<std::string>& props,
		   bool verdict=false);
  std::string file;
public:
  std::vector<std::string> anames;
  std::vector<std::string> tnames;
private:
  std::string separator;
};

#endif
