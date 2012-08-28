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
#include "adapter.hh"
#include <sys/time.h>
#include <fcntl.h>
#include <unistd.h>

class Adapter_rly08btech: public Adapter {
public:
  Adapter_rly08btech(Log& l, std::string params);
  virtual ~Adapter_rly08btech(){ if (fd>0) close(fd); }
  virtual void execute(std::vector<int>& action);
  virtual int  observe(std::vector<int> &action,bool block=false);
  virtual std::string stringify();
  virtual void set_actions(std::vector<std::string>* _actions);
  virtual bool init();
private:
  int fd;
  std::string devname;
  std::map<std::string,unsigned char> command;
};
