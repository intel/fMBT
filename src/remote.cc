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

#include "remote.hh"
#include <list>
#include <string>
#include <vector>
#include "helper.hh"
#include "windows_helper.cc"

gboolean
_g_spawn_command_line_sync (const gchar  *command_line,
                           gchar       **standard_output,
                           gchar       **standard_error,
                           gint         *exit_status,
                           GError      **error)
{
  gboolean retval;
  gchar **argv = 0;
  
  g_return_val_if_fail (command_line != NULL, FALSE);
  
  if (!g_shell_parse_argv (command_line,
			   NULL, &argv,
			   error))
    return FALSE;
  
  retval = _g_spawn_sync (NULL,
			  argv,
			  NULL,
			  G_SPAWN_SEARCH_PATH,
			  NULL,
			  NULL,
			  standard_output,
			  standard_error,
			  exit_status,
			  error);
  g_strfreev (argv);

  return retval;
}


gboolean
_g_spawn_sync (const gchar *working_directory,
              gchar **argv,
              gchar **envp,
              GSpawnFlags flags,
              GSpawnChildSetupFunc child_setup,
              gpointer u_data,
              gchar **standard_output,
              gchar **standard_error,
              gint *exit_status,
	      GError **error)
{
  GError* g=NULL;
  gboolean ret=g_spawn_sync(working_directory,argv,envp,flags,child_setup,u_data,
			    standard_output,standard_error,exit_status,&g);

  if (error)
    *error = g;

  if (g==NULL)
    return ret;

#ifdef __MINGW32__
  g=NULL;

  if (g_path_is_absolute (argv[0])) {
    return ret;
  }

  _populatesearchpath();

  for(std::list<std::string>::iterator i=_search_path.begin();
      i!=_search_path.end();i++) {
    
    gchar* tmp=g_build_filename(i->c_str(),argv[0],NULL);
    
    if (g_file_test(tmp,G_FILE_TEST_IS_REGULAR)) {
      // Let's check if file contains #! and python at the first line...

      GIOChannel *stream=g_io_channel_new_file (tmp,"r",NULL);
      
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
	    gchar** newargv=_strv_addfirst(argv,interp);
	    
	    newargv[1]=tmp;

	    ret=g_spawn_sync(working_directory,newargv,envp,flags,child_setup,u_data,
			     standard_output,standard_error,exit_status,&g);
	    
	    g_free(newargv);
	    
	    if (error)
	      *error=g;
	    
	    if (g==NULL) {
	      g_free(tmp);
	      return ret;
	    }
	    g=NULL;
	  }
	}
      }
    }
    g_free(tmp);
  }

#endif

  return ret;  
}

gboolean
_g_spawn_async_with_pipes (const gchar *working_directory,
			   gchar **argv,
			   gchar **envp,
			   GSpawnFlags flags,
			   GSpawnChildSetupFunc child_setup,
			   gpointer user_data,
			   GPid *child_pid,
			   gint *standard_input,
			   gint *standard_output,
			   gint *standard_error,
			   GError **error)
{
  GError* g=NULL;
  gboolean ret=g_spawn_async_with_pipes(working_directory,argv,envp,flags,
					child_setup,user_data,child_pid,
					standard_input,standard_output,
					standard_error,&g);

  if (error)
    *error=g;

  if (g==NULL)
    return ret;

#ifdef __MINGW32__
  g=NULL;

  if (g_path_is_absolute (argv[0])) {
    return ret;
  }

  _populatesearchpath();
  std::list<std::string>::iterator i=_search_path.begin();
  std::list<std::string>::iterator e=_search_path.end();

  gchar* argpath=NULL,*interp=NULL;
  while (_iterate(i,e,interp,argpath,argv[0])) {
    
    gchar** newargv=_strv_addfirst(argv,interp);
    
    newargv[1]=argpath;
    
    ret=g_spawn_async_with_pipes(working_directory,newargv,envp,flags,
				 child_setup,user_data,child_pid,
				 standard_input,standard_output,
				 standard_error,&g);
    
    g_free(newargv);

    g_free(interp);
    interp=NULL;

    g_free(argpath);
    argpath=NULL;
    
    if (error)
      *error=g;
    
    if (g==NULL) {
      return ret;
    }    
  }

#endif
  return ret;
}
