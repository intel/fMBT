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

#ifdef __MINGW32__
#include <list>
#include <string>
#include <string>

#include <windows.h>

std::list<std::string> _search_path;

void _searchpathappend(const char* path,std::list<std::string>& _path) {
  if (path) {
    std::vector<std::string> vec;
    std::string s(path);
    strvec(vec,s,G_SEARCHPATH_SEPARATOR_S);
    for(unsigned i=0;i<vec.size();i++) {
      _path.push_back(vec[i]);
    }
  }
}

void _populatesearchpath() {
  if (_search_path.empty()) {
    gchar *dir = NULL;
    wchar_t wdir[MAXPATHLEN];
    int n;
    
    n = GetModuleFileNameW (NULL, wdir, MAXPATHLEN);
    if (n > 0 && n < MAXPATHLEN) {
      dir = g_utf16_to_utf8 ((gunichar2*)wdir, -1, NULL, NULL, NULL);
      gchar* tmp=g_path_get_dirname(dir);
      g_free(dir);
      _search_path.push_back(tmp);
      g_free(tmp);
    }      
    
    n = GetSystemDirectoryW (wdir, MAXPATHLEN);
    if (n > 0 && n < MAXPATHLEN) {
      dir = g_utf16_to_utf8 ((gunichar2*)wdir, -1, NULL, NULL, NULL);
      _search_path.push_back(dir);
      g_free(dir);
    }
    
    n = GetWindowsDirectoryW (wdir, MAXPATHLEN);
    if (n > 0 && n < MAXPATHLEN) {
      dir = g_utf16_to_utf8 ((gunichar2*)wdir, -1, NULL, NULL, NULL);
      _search_path.push_back(dir);
      g_free(dir);
      }
    // Let's append normal path....
    _searchpathappend(g_getenv("PATH"),_search_path);      
  }
}


gchar** _strv_addfirst(gchar** str_array,gchar* first) {
  if (str_array) {
    gint i=0;
    gchar **retval;
    
    while (str_array[i])
      ++i;
    
    retval = g_new (gchar*, i + 2);
    
    retval[0]=first;
    i = 0;

    while (str_array[i]) {
	retval[i+1] = str_array[i];
	++i;
      }
    retval[i+1] = NULL;
    
    return retval;
  }
  return str_array;
}

bool _iterate(std::list<std::string>::iterator &i,
		     std::list<std::string>::iterator e,
		     gchar*& interp,gchar*& argpath,
		     gchar* arg)
{

  while(i!=e) {
    argpath=g_build_filename(i->c_str(),arg,NULL);
    i++;

    if (g_file_test(argpath,G_FILE_TEST_IS_REGULAR)) {
      // Let's check if file contains #! and python at the first line...
      GIOChannel *stream=g_io_channel_new_file (argpath,"r",NULL);
      
      if (stream) {
	gchar* line=NULL;
	size_t len=0;
	getline(&line,&len,stream);
	g_io_channel_shutdown(stream,FALSE,NULL);
	
	if (g_str_has_prefix (line,"#!")) {
	  gchar* interp=NULL;
	  if (g_strrstr(line,"python")) {
	    interp=strdup("python");
	  }
	  
	  if (interp) {
	    return true;
	  }
	}
      }
    }
  }

  return false;
}

#endif
