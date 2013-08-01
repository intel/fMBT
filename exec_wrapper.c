#include <glib.h>
#include <stdio.h>
#include <string.h>

int main(int argc,char** argv)
{
  gint exit_status;
  int i;

  char** margv;
  g_type_init ();

  margv=(char**)g_new0(char**,argc+2);
  margv[0]="C:\\Python27\\python.exe";

  margv[1]=g_find_program_in_path(argv[0]);

  if (g_str_has_suffix(margv[1],".exe")) {
    margv[1]=g_strndup(margv[1],strlen(margv[1])-4);
  }

  for(i=1;i<argc;i++) {
    margv[i+1]=argv[i];
  }

  g_spawn_sync(NULL,margv,NULL,
	       G_SPAWN_CHILD_INHERITS_STDIN,
	       NULL,NULL,
	       NULL,NULL,
	       &exit_status,NULL);
  return exit_status;  
}
