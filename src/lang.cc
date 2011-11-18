#include "dparse.h"
#include "helper.hh"

extern "C" {
extern D_ParserTables parser_tables_lang;
};

int main(int argc,char** argv) {
  char *s;
  D_Parser *p = new_D_Parser(&parser_tables_lang, 512);
  //std::string name(argv[1]);
  s=readfile(argv[1]);
  dparse(p,s,std::strlen(s));

  free_D_Parser(p);
  return 0;
}
