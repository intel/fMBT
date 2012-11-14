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

#include "history_multi.hh"
#include "helper.hh"

/*
int glob(const char *pattern, int flags,
	 int (*errfunc) (const char *epath, int eerrno),
	 glob_t *pglob);
void globfree(glob_t *pglob);
*/

#define RETURN_ERROR(s) { \
  status=false; \
  errormsg=s;   \
  return NULL; \
  }


History_multi::History_multi(Log& l, std::string _params) :
  History(l,_params), params(_params)
{

}

Alphabet* History_multi::set_coverage(Coverage* cov,
				      Alphabet* alpha)
{
  std::vector<std::string> v;
  static const std::string separator(":");
  strvec(v,params,separator);
  for(unsigned i=1;i<v.size();i++) {
    printf("Creating %s %s\n",v[0].c_str(),v[1].c_str());
    History* h=HistoryFactory::create(log,v[0],v[i]);
    if (h) {
      h->set_coverage(cov,alpha);
      if (!h->status) {
	RETURN_ERROR(h->errormsg);
      }
    } else {
      RETURN_ERROR("Creating history \""+ v[0] + ":" + v[i] + "\" failed");
    }
  }
  return NULL;
}

FACTORY_DEFAULT_CREATOR(History, History_multi, "multi")
