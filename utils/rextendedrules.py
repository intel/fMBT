#!/usr/bin/env python
# coding: iso-8859-1
# Copyright (c) 2006-2010 Tampere University of Technology
# 
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


"""
tema.rextendedrules 0.3b

This program takes extended rules file with regular expressions as
input and gives extended rules as output. The output can be redirected
to tvt.extendedrules program.

Usage:

    tema.rextendedrules [options] <inputfile> [outputfile]

Options:
    --help     Print this help.
    --re-help  Show help on regular expressions.
    --force    Overwrite output file if it exists.
    --Wall     Print warnings if rows of input file
               could not be parsed (otherwise the rows
               are silently skipped).

If input (output) file name is replaced by '-', standard input
(output) is used instead.

Copyright (C)
    2004-2005 by VARG research group at Tampere University of Technology,
              author Antti Kervinen, teams@cs.tut.fi.
"""

##
# 0.21b-> 0.3b
#    changes in behavior:
#    - does not print a rule if there is an (lsts,action) pair where
#      action is not in the alphabet of the lsts
#    - multiple lsts synchronisations are checked in the end
#      after broken rules (see previous change) are removed
#
#
# 0.2b -> 0.21b
#    new features:
#    - $E(expression)E is replaced by the value of /expression/
#      evaluated in Python.
#
# 0.11 -> 0.2b
#    new features:
#    - ALL and OPT keywords for introducing rules with
#      variable number of participant processes.
#    - process ids can be given as arrays
#    - empty and comment rows are be copied to output
#    
#
# 0.1 -> 0.11
#    bug fixes: handling tau, prints now all process names,
#    can be run with only one argument (default output is stdout)

import lsts

import sys
import re
import copy
import os

RULEROW=0
COMMENTROW=1

class RextendedrulesError(Exception): pass

def error(s,exitval=1):
    print >>sys.stderr,"rextendedrules: %s" % s
    sys.exit(exitval)

### TVT-like routine for argument handling
def parse_args(argv):
    try:
        # parse (and remove) options
        if len(argv)==1 or "--help" in argv:
            print __doc__
            sys.exit(0)

        if "--re-help" in argv:
            print re.__doc__
            sys.exit(0)

        overwriteoutput=(0,1)["--force" in argv]
        if overwriteoutput: argv.remove("--force")

        parsewarnings=(0,1)["--Wall" in argv]
        if parsewarnings: argv.remove("--Wall")

        # parse input and output files

        if len(argv)==2: argv.append("-") # default output is stdout

        if len(argv)!=3: raise Exception("Illegal arguments. Try --help.")


        inputfile=argv[1]
        
        

        if argv[2]=="-": outputfile=argv[2]
        elif not overwriteoutput and os.path.isfile(argv[2]):
            raise Exception("'%s' already exists. Use --force to overwrite." % argv[2])
        else: outputfile=argv[2]

    except SystemExit, num:
        sys.exit(num)
    except Exception, e:
        error(e)

    return (parsewarnings,inputfile,outputfile)

### end of argument routine

class Rextfile_parser:
    
    def __init__(self):
        self.__procrowre = re.compile('\s*([^=\s]+)\s*=\s*"([^"]+)"')
        self.__procarray = re.compile('\[([0-9]+)\s*\.\.\s*([0-9]+)\]')

        self.__rulerowre = re.compile('^\s*([A-Z]*\(.*\))\s*->\s*"([^"]+)"\s*$')
        # single syncronisating action spec on the left of ->
        self.__syncactre = re.compile('([A-Z]*)\(\s*([^,\s]*)\s*,\s*"([^"]+)"\s*\)')

        # comment row
        self.__commentrow = re.compile('^(\s*(#.*|))$')

        # regexps are in ${regex} and replace numbers $=nn.
        self.__regex = re.compile('\$\{([^}]+)\}')

        # evalexps are in $(evalex), they are evaluated when all
        # regexps have been expanded, unless they are inside a regular
        # expression. In the latter case they are evaluated just
        # before the regular expression is expanded
        self.__evalex = re.compile('\$E\(((?!\)E).*)\)E')

    def commentrow(self,s):
        m = re.match(self.__commentrow,s)
        if m:
            return m.group(1)
        return None

    def processrow(self,s):
        m = re.match(self.__procrowre,s)
        if m:
            lsts_key = m.group(1)
            lsts_filename = m.group(2)
            return lsts_key,lsts_filename
        return None

    def rulerow(self,s):
        m = re.match(self.__rulerowre,s)
        if m:
            leftspecs=re.findall(self.__syncactre,m.group(1))
            rightspec=m.group(2)
            if len(leftspecs)>0:
                return leftspecs,rightspec
        return None

    def expand_procarray(self,s):
        names=[s]
        for m in self.__procarray.finditer(s):
            grouplen=len(m.group(0))
            fill,newnames='='*grouplen,[]
            for i in xrange(int(m.group(1)),int(m.group(2))+1):
                # in 2.4 python: ns=str(i).rjust(grouplen,'=')
                ns=('%s%s' % (fill,i))[-grouplen:]
                for n in names:
                    newnames.append(n[:m.start()]+ns+n[m.end():])
            names=newnames
        return [s.replace('=','') for s in names]

    def pop_next_regex(self,s):
        m = self.__regex.search(s)
        if m:
            return s[:m.start(1)-2],m.group(1),s[m.end(1)+1:]
        return s,None,""

    def replace_next(self,rule,repl,match_rhs=1):
        try:
            replp=re.compile('\$\='+str(rule[2])+'\.')
        except Exception, e:
            print rule
            print e
            
        try:
            for triplet_index,triplet in enumerate(rule[0]):
                rule[0][triplet_index]=(rule[0][triplet_index][0],
                                        replp.sub(repl,triplet[1]),
                                        replp.sub(repl,triplet[2]))
                if match_rhs: rule[1]=replp.sub(repl,rule[1])
        except Exception, e:
            print rule
            print e
        
        rule[2]+=1
        return rule

    def expand_evalexps(self,s):
        ee = self.__evalex # evaluation expression pattern $E(...)E
        try:
            if ee.findall(s)==[]:
                return s
            else:
                return ee.sub('%s',s) % \
                    tuple( [eval(expr) for expr in ee.findall(s)] )
        except Exception, e:
            raise RextendedrulesError("invalid Python evaluation in '%s'%s(%s)%s" % (s,os.linesep,e,os.linesep))
#            sys.stderr.write("ERROR: tvt.rextendedrules: invalid Python evaluation in '%s'\n(%s)\n" % (s,e))
#            sys.exit(1)

def rextendedrules(working_dir, parse_warnings,input_fileobj,output_fileobj):

    parser=Rextfile_parser()
    filenames={}
    alphabets={}
    lstsnumber={}
    rules=[]
    alreadyprintedrules={}

    # rules = [
    #  [ [ (quant,lstskey, actionname), ..., (quant,key_n, name_n) ],
    #    result,
    #    next_expanded_re_number,
    #    ruletype ::= RULEROW | COMMENTROW,
    #    row_number_in_input_file,
    #    dict: participant -> number of appearances in the row,
    #  ],
    #  similar rule row 2
    #  ...
    #  ]

    # Parse rextended rules
    for rowindex,l in enumerate(input_fileobj):
        row=parser.processrow(l)
        if row:
            for processname in parser.expand_procarray(row[0]):
                filenames[processname]=row[1]
                lstsnumber[processname]=len(filenames)
            continue
        row=parser.rulerow(l)
        if row:
            rules.append([row[0],row[1],1,RULEROW,rowindex+1,{}])
            continue
        row=parser.commentrow(l)
        if row:
            rules.append([row,0,0,COMMENTROW,rowindex+1])
            continue
        if parse_warnings:
            sys.stderr.write("WARNING: rextendedrules: could not parse row %s:%s\t'%s'%s" % (rowindex+1,os.linesep,l.strip(),os.linesep))

    # Get actionnames sections of mentioned lsts files
    for key in filenames:
        r=lsts.reader()
        try:
            r.read(open(os.path.join(working_dir,filenames[key]),'r'))
            alphabets[key]=r.get_actionnames()
        except Exception, e:
            raise RextendedrulesError("(in file '%s'): %s%s" % (filenames[key],e,os.linesep))
#            sys.stderr.write("ERROR: tvt.rextendedrules (in file '%s'): %s\n" % (filenames[key],e))
#            import traceback
#            traceback.print_exc(file=sys.stderr)
#            sys.exit(1)
    del r # no need for reader anymore.


    ### Print LSTS files and their numbers
    lsts_id_by_num={}
    for k in lstsnumber: lsts_id_by_num[lstsnumber[k]]=k
    for n in xrange(1,max(lsts_id_by_num.keys())+1):
        output_fileobj.write('%s="%s"%s' % (n,filenames[lsts_id_by_num[n]],os.linesep))

    # Handle the rules in the original order. The rules list will be
    # handled as a stack, so we have to reorder it.
    rules=rules[::-1]

    def create_regexp(s,rownumber):
        # return None, if s has no regexps, otherwise
        # builds and returns a new regular expression
        prefix,regex,suffix=parser.pop_next_regex(s)
        if not regex:
            return None
        newregex=""
        while regex:
            newregex+=re.escape(prefix)+"("+parser.expand_evalexps(regex)+")"
            prefix,regex,suffix=parser.pop_next_regex(suffix)
        newregex+=re.escape(prefix)
        try:
            retval=re.compile(newregex)
            return retval
        except:
            raise RextendedrulesError("in row %s invalid regular expression: '%s'%s" % (rownumber,s,os.linesep))
#            sys.stderr.write("ERROR: tvt.rextendedrules: in row %s invalid regular expression: '%s'\n" % (rownumber,s))
#            sys.exit(1)

    while rules:
        # 0. Take a rule

        r=rules.pop()

        if r[3]==COMMENTROW:
            output_fileobj.write("%s%s" % (r[0],os.linesep))
            continue

        # assume: r[3]==RULEROW
        # quantifier ::= empty | ALL | OPT
        for left_index,left_contents in enumerate(r[0]):
            quantifier,lstskey,actionname=left_contents

            # 1. If quantifier of a participant is ALL,
            # extend it to many participants
            if quantifier=='ALL':
                newre=create_regexp(lstskey,r[4])
                if newre:
                    cr=copy.deepcopy(r)
                    cr[0]=[]
                    for k in alphabets.keys():
                        m=newre.match(k)
                        if m:
                            appearcount=r[5].get(k,0)
                            if appearcount!=0: continue # skip already participating lstss
                            r[5][k]=1
                            cr[0].append( ('OPT',k,actionname) )
                            for g in m.groups():
                                parser.replace_next(cr,g,match_rhs=0)
                            cr[2]=cr[2]-len(m.groups())
                    cr[0]=r[0][:left_index] + cr[0] + r[0][left_index+1:]
                    rules.append(cr)
                    break
                else:
                    # no regexp but quantifier == ALL
                    # handling is equal to OPT.
                    r[0][left_index]=('OPT',lstskey,actionname)
                    quantifier='OPT'
                    # no need to break here
            # endif --- after this quantifier != ALL

            # 2. Search for regular expressions in lstskey part of a
            # action specification in the left hand side of the rule
            newre=create_regexp(lstskey,r[4])
            if newre:
                matchcount=0
                for k in alphabets.keys():
                    m=newre.match(k)
                    if m:
                        matchcount+=1

                        # 2.1 If quantifier=='' or quantifier=='OPT',
                        # create a new rule for each lstskey that matched
                        # to the regexp. In the new rule, replace every
                        # '$=n.' by the string that matched the rexexp.
                        # part. Add all the resulting rules to the rules
                        # stack.

                        cr=copy.deepcopy(r)
                        cr[5][k]=cr[5].get(k,0)+1
                        if quantifier=='OPT':
                            if cr[5][k]>1:
                                cr[0]=cr[0][:left_index]+cr[0][left_index+1:]
                                break # silently ignore participant
                            cr[0]=[ (quantifier,k,actionname) ]
                            for g in m.groups():
                                parser.replace_next(cr,g,match_rhs=0)
                            cr[0]=r[0][:left_index] + cr[0] + r[0][left_index+1:]
                            cr[2]=cr[2]-len(m.groups)
                        elif quantifier=='':
                            if cr[5][k]>1:
                                #sys.stderr.write("ERROR: tvt.rextendedrules: in row %s LSTS '%s' synchronised more than once.\n" % (r[4],k))
                                #sys.exit(1)
                                pass # hope that the problem goes away before last check

                            cr[0][left_index]=(quantifier,k,actionname)
                            for g in m.groups():
                                parser.replace_next(cr,g)

                        rules.append(cr)
                break
            if quantifier=='OPT' and (not lstskey in alphabets and matchcount==0):
                r[0]=r[0][:left_index]+r[0][left_index+1:]
                rules.append(r)
                break

            # 3. Similarly to 2., handle the actionname.
            # lstskey should be valid (it did not contain regexp).
            try:
                actionlist=alphabets[lstskey]
            except KeyError:
                if quantifier=='OPT':
                    r[0]=r[0][:left_index]+r[0][left_index+1:]
                    rules.append(r)
                    break
                raise RextendedrulesError("in row %s unknown LSTS '%s'%s " % (r[4],lstskey,os.linesep))
#                sys.stderr.write("ERROR: tvt.rextendedrules: in row %s unknown LSTS '%s'\n " % (r[4],lstskey))
#                sys.exit(1)
            matchcount=0
            newre=create_regexp(actionname,r[4])
            if newre:
                for a in actionlist:
                    m=newre.match(a)
                    if m:
                        matchcount+=1
                        cr=copy.deepcopy(r)
                        if quantifier=='OPT':
                            cr[0]=[ ('',lstskey,a) ]
                            for g in m.groups():
                                parser.replace_next(cr,g,match_rhs=0)
                            cr[0]=r[0][:left_index]+cr[0]+r[0][left_index+1:]

                        if quantifier=='':
                            cr[0][left_index]=('',lstskey,a)
                            for g in m.groups():
                                parser.replace_next(cr,g)

                        rules.append(cr)
                break
            if quantifier=='OPT':
                # no need to quantify anymore: if no match then remove participant
                if (not newre and not actionname in alphabets[lstskey]):
                    r[0]=r[0][:left_index]+r[0][left_index+1:]
                elif actionname in alphabets[lstskey]:
                    r[0][left_index]=('',lstskey,actionname)
                rules.append(r)
                break
        else: # for-loop was not breaked out => rule does not contain regexps
            # it is ready to be printed
            rulestr=""
            syncactions=[]
            resultaction=""
            lstsappearances={}
            failed=0
            for quantifier,lstskey,actionname in r[0]:
                if quantifier!='': print 'hell with',r

                if actionname in alphabets[lstskey]:
                    thislsts=lstsnumber[parser.expand_evalexps(lstskey)]
                    syncactions.append((thislsts,parser.expand_evalexps(actionname)))
                    lstsappearances[thislsts]=lstsappearances.get(thislsts,0)+1
                else:
                    failed=1
            if not failed: # check that no LSTS appears in any line more than once
                syncactions.sort()
                resultaction=parser.expand_evalexps(r[1])
                if str(syncactions)+resultaction in alreadyprintedrules:
                    failed=1
                else:
                    alreadyprintedrules[str(syncactions)+resultaction]=1
                    rulestr=' '.join(['(%s,"%s")' % (l,a) for l,a in syncactions])
                if [ v for v in lstsappearances.values() if v>1 ]:
                    raise RextendedrulesError("the same LSTS synchronized more than once in rule:%s    '%s' (row %s)" % (os.linesep,rulestr,r[4]))
#                    sys.stderr.write("ERROR: tvt.rextendedrules: the same LSTS synchronized more than once in rule:\n    '%s' (row %s)" % (rulestr,r[4]))
#                    sys.exit(1)

            if not failed:
                output_fileobj.write('%s-> %s%s' % (rulestr,('"'+parser.expand_evalexps(r[1])+'"',0)[r[1].upper()=="TAU"],os.linesep))


if __name__ == "__main__":
    parse_warnings,input_filename,output_filename = parse_args(sys.argv)
    infile = None
    outfile = None
    try:
        try:
            if input_filename == "-":
                infile = sys.stdin
            else:
                infile = open(input_filename,'r')
            if output_filename == "-":
                outfile = sys.stdout
            else:
                outfile = open(output_filename,'w')

            rextendedrules(os.getcwd(), parse_warnings, infile, outfile )
        except RextendedrulesError,e:
            error(e)
        except KeyboardInterrupt,e:
            sys.exit(1)
        except:
            import traceback
            traceback.print_exc(file=sys.stderr)
            sys.exit(1)
    finally:
        if outfile and output_filename != "-":
            outfile.close()
        if infile and input_filename != "-":
            infile.close()
