/* 
    $URL: http://manta.univ.gda.pl/svn/wb/parsing/dparser/D/driver_parsetree.c $
    $Revision: 1.1 $
*/

#include <stdio.h>
#include <string.h>

#include "dparse_tree.h"

char *sbuf_read(char *pathname);  /* defined in util.h */

extern D_ParserTables parser_tables_gram;

int main(int argc, char *argv[]) {
  char *buf;
  D_ParseNode *pn;
  /* any number greater than sizeof(D_ParseNode_User) will do;
     below 1024 is used */
  D_Parser *p = new_D_Parser(&parser_tables_gram, 1024); 
  p->save_parse_tree = 1;

  if (argc!=2) {
    fprintf(stderr,"U¿ycie: %s FILE_to_parse\n",argv[0]);
    return -1;
  } else {
    buf = sbuf_read(argv[1]);
    if (buf == NULL) {
      fprintf(stderr, "error: empty buf\n");
      return -2;
    }
  }
  printf("file: %s\n", argv[1]);
  printf("----------\n%s", buf);
  printf("----------\n");

  if ((pn=dparse(p, buf, strlen(buf))) && !p->syntax_errors) {
    printf("\nparse tree\n");
    printf("----------\n");
    print_parsetree(parser_tables_gram, pn, NULL, NULL);
    printf("\n");
  } else {
    printf("\nfailure\n");
  }
  return 0;
}

