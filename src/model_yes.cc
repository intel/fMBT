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

#include "model_yes.hh"
#include "helper.hh"

void Model_yes::set_model(Alphabet* m) 
{
  model=m;
  std::vector<std::string>& an=model->getActionNames();
  std::vector<std::string>& pn=model->getSPNames();

  action_names=an;
  prop_names=pn;

  precalc_input_output();

  for(unsigned i=1;i<action_names.size();i++) {
    if (!is_output(i)) {
      iact.push_back(i);
    }
    act.push_back(i);
  }

}

void Model_yes::set_props(std::string p)
{
  std::vector<std::string> v;
  props.clear();
  static std::string sep(" ");
  strvec(v,p,sep);
  for(unsigned i=0;i<v.size();i++) {
    props.push_back(find(prop_names,v[i]));
  }
}

void Model_yes::set_props(int* p,int c)
{
  props.assign(p,p+c);
}
