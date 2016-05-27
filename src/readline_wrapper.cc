#include "config.h"

#include <cstdio>
#include <cstdlib>
#include <cstring>

#if defined(DROI) || defined(__MINGW32__)
char* READLINE(const char* prompt,FILE* ostream)
{
    char *s = (char*)malloc(1024);
    if (s == NULL)
        return NULL;
    fprintf(ostream, "%s", prompt);
    if (fgets(s, 1024, stdin) == NULL) {
        // end of input
        std::free(s);
        return NULL;
    }
    // strip trailing LF, CR, CRLF, LFCR
    s[strcspn(s, "\r\n")] = 0;
    return s;
}
#else
#ifdef USE_GNU_READLINE
#include <readline/readline.h>
#include <readline/history.h>

char* READLINE(const char* prompt,FILE* ostream)
{
  return readline(prompt);
}
#else
#ifdef USE_EDITLINE
/* Let's use editline... */
extern "C" {
#include <editline.h>
};
char* READLINE(const char* prompt,FILE* ostream) {
  fprintf(ostream,"%s",prompt);
  return readline();
}
#else
/* Defaults to BSD editline readline.. */
#include <editline/readline.h>
extern FILE             *rl_instream;
extern FILE             *rl_outstream;
char            *readline(const char *);
char* READLINE(const char* prompt,FILE* ostream) {
  rl_outstream=ostream;
  return readline(prompt);
}
#endif
#endif
#endif // ifdef DDROI else
