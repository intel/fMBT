#include <stdio.h>
#include <getopt.h>

int main(int argc,char * const argv[])
{
  int c;
  int ac=0;
  int stack[10];
  int sp=0;
  FILE* in=stdin;
  FILE* out=stdout;

  while ((c = getopt_long (argc, argv, "o:i:", NULL, NULL)) != -1)
    switch (c)
      {
      case 'o':
	out=fopen(optarg,"w");
	break;
      case 'i':
	in=fopen(optarg,"r");
	break;
      default:
	return 1;
      }

  if (optind != argc)  {
    return 2;
  } 

  fprintf(out,"P(init0, \"gt:istate\") ->\n");
  fprintf(out,"P(init0, \"gt:istate\")\n");
  c=getc(in);

  while (c!=EOF) {
    switch(c) {
    case '+': 
      fprintf(out,"T(init%i, \"iinc\", init%i)\n",
	     ac,ac+1);
      ac++;
      break;
    case '-': 
      fprintf(out,"T(init%i, \"idec\", init%i)\n",
	     ac,ac+1);
      ac++;
      break;
    case '>':
      fprintf(out,"T(init%i, \"inext\", init%i)\n",
	     ac,ac+1);
      ac++;
      break;
    case '<':
      fprintf(out,"T(init%i, \"iprev\", init%i)\n",
	     ac,ac+1);
      ac++;
      break;
    case '.':
      fprintf(out,"T(init%i, \"iprint\", init%i)\n",
	     ac,ac+1);
      ac++;
      break;
    case ',':
      fprintf(out,"T(init%i, \"iinput\", init%i)\n",
	     ac,ac+1);
      ac++;
      break;
    case '[':
      stack[sp]=ac;
      ac++;
      sp++;
      break;

    case ']':
      sp--;
      fprintf(out,"T(init%i, \"imemz\", init%i)\n",
	     stack[sp],ac+1);
      fprintf(out,"T(init%i, \"imemz\", init%i)\n",
	     ac,ac+1);

      fprintf(out,"T(init%i, \"imemnz\", init%i)\n",
	     stack[sp],stack[sp]+1);
      fprintf(out,"T(init%i, \"imemnz\", init%i)\n",
	     ac,stack[sp]+1);
      
      ac++;
      break;
    }
    c=getc(in);
  }

  return 0;
}
