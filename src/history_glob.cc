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
#ifndef __MINGW32__
#include "history_glob.hh"
#include "helper.hh"
#include <glob.h>
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


History_glob::History_glob(Log& l, std::string _params) :
  History(l,_params), params(_params)
{
  /*
  void *memset(void *s, int c, size_t n);
  */
  memset(&gl,0,sizeof(glob_t));
}

Alphabet* History_glob::set_coverage(Coverage* cov,
				     Alphabet* alpha)
{
  std::vector<std::string> v;
  static const std::string separator(":");
  strvec(v,params,separator);
  for(unsigned i=1;i<v.size();i++) {
    glob(v[i].c_str(),GLOB_DOOFFS | GLOB_APPEND, NULL, &gl);
  }
  for(size_t i=0;i<gl.gl_pathc;i++) {
    printf("Creating %s:%s\n",v[0].c_str(),gl.gl_pathv[i]);
    History* h=HistoryFactory::create(log,v[0],gl.gl_pathv[i]);
    if (h) {
      h->set_coverage(cov,alpha);
      if (!h->status) {
	RETURN_ERROR(h->errormsg);
      }
    } else {
      RETURN_ERROR("Creating history \""+ v[0] + ":" + gl.gl_pathv[i] +
		   "\" failed");
    }
  }
  return NULL;
}

FACTORY_DEFAULT_CREATOR(History, History_glob, "glob")
#endif
