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
#include "adapter.hh"
#include <linux/videodev2.h>

class Adapter_v4l2: public Adapter {
public:
  Adapter_v4l2(Log& l, std::string params = "");
  virtual void execute(std::vector<int>& action_list);
  virtual bool observe(std::vector<int> &action,bool block=false);
private:
  int fd;
  std::string filename;
  int brightness;
  struct v4l2_format resolution;
};
