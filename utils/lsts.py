#!/usr/bin/env python2
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
Library for reading and writing LSTSs.

This library provides LSTS reader and writer classes, and a lsts
class.

Note that in the files indexing of states starts from 1, but in the
data structures that the reader and writer classes use, it starts from
0.

Note also that the action name with index 0 should always be "tau". It
will not be written in the action names section of the file, but it
may still appear in the transitions.

Only low level access to History section is provided: every item in
history list is a row in History section without indentation.

***

Example I: write a three-state LSTS to file out.lsts:

import lsts

w = lsts.writer( file("out.lsts","w") )

w.set_actionnames( ["tau","action1","action2"] )
w.set_transitions( [ [(1,0),(0,0)], [(0,2),(2,1)], [] ] )
w.write()

***

Example II: read lsts from stdin, rename the first non-tau action and
write the lsts to stdout.

import sys
import lsts

r = lsts.reader(sys.stdin)

r.get_actionnames()[1]="new name"

lsts.writer(sys.stdout,r)

***

Example III: list action names used in the transitions

import lsts

r = lsts.reader(sys.stdin)

used_actions=[]

for source_state, transition_list in enumerate(r.get_transitions()):

    for dest_state, action_number in transition_list:

        if not action_number in used_actions:
            used_actions.append( action_number )
            print r.get_actionnames()[ action_number ]

***

Helper classes and functions

class fakefile can be used to create a file-like object from a
string. The object can be used for reading and writing LSTSs. For
example, if string s contains an LSTS

r=lsts.reader(fakefile(s))
r.read()

reads the LSTS in s.

props_by_states(lsts_object) returns table indexed with state
numbers. The table includes lists of state proposition numbers. For
example,

props_by_states(r)[42]

returns list of numbers of propositions true in state 42. To convert
the number of a state proposition to a name, index alphabetically
ordered list of state proposition keys with it:

stateproplist=r.get_stateprops().keys()
stateproplist.sort()
name_of_prop=stateproplist[num_of_a_stateprop]

"""

version="0.522 svn"

# 0.490 -> 0.522 support for dos lines (carriage returns are removed)
# 0.110 -> 0.490 support for multirow action names
# 0.55 -> 0.110 lsts file objects can be read and written already in
#               the constructor.

# 0.53 -> 0.55 stateprops numbered in the order of occurence in the lsts file
#              (alphabetical order). Documentation changed accordingly.

# 0.52 -> 0.53 bugfix: state props numbered off-by-one
# 0.52 -> 0.53 bugfix: reading multi-line transitions and state props
# 0.52 -> 0.53 props_by_states-helper function
# 0.52 -> 0.53 psyco is used if possible

# 0.50 -> 0.52 added support for state prop ranges "x..y"

from sys import stderr

class fakefile:
    """
    fakefile(string) is a file-like object that contains the
    string. It implements readline and write methods and nothing else.
    This class can be used as input and output file of the reader and
    the writer classes. The contents of the file are in attribute s.
    """
    def __init__(self,lstscontents):
        self.s=lstscontents
    def readline(self):
        l=self.s[:self.s.find("\n")+1]
        self.s=self.s[self.s.find("\n")+1:]
        return l
    def write(self,s):
        self.s+=s


def props_by_states(lsts_object):
    """props_by_states(lsts_object) -> state_table

    If propositions x and y (and no other propositions) are true in
    state s, then state_table[s]==[x,y]. s, x and y are natural
    numbers. To obtain the name of the proposition x, use

    stateproplist=r.get_stateprops().keys()
    stateproplist.sort()
    name_of_prop=stateproplist[num_of_a_stateprop]
    """
    statetbl=[ [] for x in xrange(lsts_object.get_header().state_cnt)]
    propdict=lsts_object.get_stateprops()
    propkeys = propdict.keys()
    propkeys.sort()
    for propindex,prop in enumerate(propkeys):
        for state in propdict[prop]:
            statetbl[state].append(propindex)
    return statetbl


class _header:
    pass

class lsts:
    def __init__(self):
        self._history=[]

        self._header=_header()
        self._header.state_cnt=0
        self._header.action_cnt=0
        self._header.transition_cnt=0
        self._header.initial_states=0

        self._actionnames=[]
        self._transitions=[]
        self._stateprops={} # state prop name -> list of states
        self._layout=[]

    def set_actionnames(self,actionnames):
        """
        Parameters:

        - actionnames is a list of strings

        Notes:

        This method modifies Action_cnt field in the header.
        """
        if len(actionnames) > 0 and actionnames[0]=="tau":
            self._actionnames=actionnames
        else:
            stderr.write('LSTS.PY: warning: set_actionnames did not receive "tau".\n')
            self._actionnames=["tau"]+actionnames
        self._header.action_cnt=len(self._actionnames)-1


    def set_transitions(self,transitions):
        """
        Parameters:

        - transitions should be a list of list of pairs, where
        transitions[i] is a list of pairs (dest_state, action_index)
        that describe leaving transitions from state i. If there are
        no transitions from state i, then transitions[i] is empty
        list.

        dest_state and action_index are indexes to transitions and
        actionnames lists. That is, they may have values from 0 to
        len(list)-1.

        Notes:

        This method modifies State_cnt and Transition_cnt fields in
        the header.
        """
        self._transitions=transitions
        self._header.state_cnt=len(transitions)
        self._header.transition_cnt=0
        for s in transitions:
            self._header.transition_cnt+=len(s)

    def set_stateprops(self,stateprops):
        """
        Parameters:

        - stateprops should be a dictionary whose keys are state
          proposition names and values are lists of state numbers.

        Notes:

        This method modifies State_prop_cnt field in the header.
        """
        self._stateprops=stateprops
        self._header.state_prop_cnt=len(self._stateprops)

    def set_layout(self,layout):
        """
        Parameters:

        - layout should be a list of pairs (xcoord, ycoord), indexed
          with state numbers.
        """
        self._layout=layout

    def get_actionnames(self):
        return self._actionnames

    def get_transitions(self):
        return self._transitions

    def get_stateprops(self):
        return self._stateprops

    def get_layout(self):
        return self._layout

    def get_history(self):
        return self._history

    def get_header(self):
        return self._header


class writer(lsts):
    """
    LSTS writer class
    """

    def __init__(self,file=None,lsts_object=None):
        """
        Parameters:

        - Optional parameter 'file' should provide method
        'write'. Output will be written to this object. Valid objects
        are, for example, files opened for writing and sys.stdout.

        - Optional parameter lsts_object should be an instance of lsts
         (or reader or writer) class. New header will be automatically
         generated based on action names and transitions of the lsts
         object.

        - If both optional arguments are provided, the lsts object is
          immediately written to the file. In this case, for backward
          compatibility, the first call of write method will not do
          anything the writing target is the same file object.
        """
        self._written_in_constructor=None # this file has been written
        lsts.__init__(self)
        self.__file=file

        if isinstance(lsts_object,lsts):
            self.set_actionnames( lsts_object.get_actionnames() )
            self.set_transitions( lsts_object.get_transitions() )
            self.set_stateprops( lsts_object.get_stateprops() )
            self.set_layout( lsts_object.get_layout() )
            self._header.initial_states=lsts_object.get_header().initial_states

        if file!=None and lsts_object!=None: # write immediately
            self.write()
            self._written_in_constructor=file

    def write(self,file=None,stateprop_order=None):
        """
        Parameters:

        - optional parameter file is the same as in __init__.

        Notes:

        Writes all lsts information to the given file object.
        """
        if not file:
            file=self.__file

        if self._written_in_constructor==file:
            self._written_in_constructor=None
            return

        file.write("Begin Lsts\n\n")

        file.write("Begin History\n")
        for num,s in enumerate(self._history):
            file.write("\t"+str(num+1)+"\n")
            file.write("\t\""+s+"\"\n")

        file.write("End History\n\n")

        file.write("Begin Header\n")
        file.write(" State_cnt = " + str(self._header.state_cnt) + "\n")
        file.write(" Action_cnt = " + str(self._header.action_cnt) + "\n")
        file.write(" Transition_cnt = " + str(self._header.transition_cnt) + "\n")
        if self._stateprops:
            file.write(" State_prop_cnt = " + str(self._header.state_prop_cnt) + "\n")
        file.write(" Initial_states = " + str(self._header.initial_states+1) + ";\n")
        file.write("End Header\n\n")

        file.write("Begin Action_names\n")
        for ai,a in enumerate(self._actionnames[1:]):
            file.write(" "+str(ai+1)+' = "'+a.replace('"','\\"')+'"\n')
        file.write("End Action_names\n\n")

        if self._stateprops:
            file.write("Begin State_props\n")
            if stateprop_order == None:
                propnames=self._stateprops.keys()
                propnames.sort()
            else:
                propnames = stateprop_order
            for key in propnames:
                file.write('  "%s" :' % key.replace('"','\\"'))
                for v in self._stateprops[key]:
                    file.write(' %s' % (v+1))
                file.write(';\n')
            file.write("End State_props\n\n")

        file.write("Begin Transitions\n")
        for si,s in enumerate(self._transitions):
            file.write(" "+str(si+1)+":")
            for (dest_state,action_index) in s:
                file.write(" "+str(dest_state+1)+","+str(action_index))
            file.write(";\n")
        file.write("End Transitions\n\n")

        if self._layout:
            file.write("Begin Layout\n")
            for statenum, xcoor, ycoord in [(num, val[0], val[1])
                                            for num, val in enumerate(self._layout)
                                            if val!=None]:
                file.write(' %s %s %s\n' % (statenum+1, xcoor, ycoord))
            file.write("End Layout\n")

        file.write("End Lsts\n")


class reader(lsts):
    def __init__(self,file=None):
        """
        Parameters:

        - Optional parameter file should provide method 'read'. Valid
        objects are, for example, files opened for reading and
        sys.stdin. If file_object is given, the file is immediately
        read, so there is no need to call read method afterwards."""

        lsts.__init__(self)
        self.__already_read=0
        self.__file=file
        self.__sections=["begin lsts",
                         "begin history","end history",
                         "begin header","end header",
                         "begin action_names", "end action_names",
                         "begin transitions", "end transitions",
                         "begin state_props", "end state_props",
                         "begin layout", "end layout",
                         "end lsts"]
        import re
        self.__headerrow=re.compile('\s*(\S+)\s*=\s*([0-9]+)[^0-9]')
        self.__actionnamerow=re.compile('\s*([0-9]+)\s*=\s*"(([^"]|\\")*)"')
        self.__actionnamemultirow_start1=re.compile('\s*([0-9]+)\s*=\s*"([^\\\\]*)\\\\\^\s*$')
        self.__actionnamemultirow_start2=re.compile('\s*([0-9]+)\s*=\s*$')
        self.__actionnamemultirow_cont=re.compile('\s*\^([^\\\\]*)\\\\\^')
        self.__actionnamemultirow_end=re.compile('\s*\^([^"]*)"')
        self.__transitionrow=re.compile('\s*([0-9]+)[:\s]+(.*)\s*;')
        trowc1=re.compile('{[^}]*}|"[^"]*"') # transition row cleaner 1
        trowc2=re.compile(',')
        self.__cleanrow=lambda s:trowc2.sub(' ',trowc1.sub(' ',s))
        self.__stateproprow=re.compile('\s*"(([^"]|\\")*)"\s*:\s*([.0-9\s]*);')

        if file:
            self.read()
            self.__already_read=1
    def read(self,file=None):
        """
        """
        if self.__already_read:
            self.__already_read=0
            return
        if not file:
            file=self.__file
        sidx=0 # index of section that we expect to read next
        secs=self.__sections
        layout_rows=[]
        l=file.readline()
        while l:
            l=l.replace(chr(0x0d),'')
            if l.strip().lower() in secs: # move to the next section
                sidx=secs.index(l.strip().lower())

            elif secs[sidx]=="begin history":
                self._history.append(l.strip())

            elif secs[sidx]=="begin header": # parse a header row
                res=self.__headerrow.search(l)
                if res and int(res.group(2))>0:
                    if res.group(1).lower()=="action_cnt":
                        self._actionnames=["tau"] + ['N/A' for i in xrange(0,int(res.group(2)))]
                        self._header.action_cnt=int(res.group(2))
                        actionname_in_multirow=-1
                    elif res.group(1).lower()=="state_cnt":
                        self._header.state_cnt=int(res.group(2))
                        self._transitions=[ [] for _ in xrange(0,self._header.state_cnt) ]
                        self._layout=[None for _ in xrange(self._header.state_cnt)]
                    elif res.group(1).lower()=="transition_cnt":
                        self._header.transition_cnt=int(res.group(2))
                    elif res.group(1).lower()=="state_prop_cnt":
                        self._header.state_prop_cnt=int(res.group(2))
                    elif res.group(1).lower()=="initial_states":
                        self._header.initial_states=int(res.group(2))-1 # only one allowed (BAD)

            elif secs[sidx]=="begin action_names": # parse an action name row
                res=self.__actionnamerow.search(l)
                if res and int(res.group(1))>0:
                    self._actionnames[int(res.group(1))]=res.group(2).replace('\\"', '"')
                    actionname_in_multirow=-1
                else:
                    if actionname_in_multirow==-1:
                        res=self.__actionnamemultirow_start1.search(l)
                        if res:
                            # store the number of the action whose name
                            # is given in multiple rows
                            actionname_in_multirow=int(res.group(1))
                            self._actionnames[actionname_in_multirow]=res.group(2)
                        else: # real hack. parse 'number = \n "action name"'
                            res=self.__actionnamemultirow_start2.search(l)
                            if res:
                                nextline=file.readline()
                                while nextline.strip()=="": nextline=file.readline()
                                self._actionnames[int(res.group(1))]=\
                                    nextline.split('"',1)[1].rsplit('"',1)[0]
                    else:
                        res=self.__actionnamemultirow_cont.search(l)
                        if res:
                            self._actionnames[actionname_in_multirow]+=res.group(1)
                        else:
                            res=self.__actionnamemultirow_end.search(l)
                            if res:
                                self._actionnames[actionname_in_multirow]+=res.group(1)
                                actionname_in_multirow=-1

            elif secs[sidx]=="begin transitions": # parse a transition row
                res=self.__transitionrow.search(l)
                if res and int(res.group(1))>0:
                    starting_state=int(res.group(1))-1
                    l=self.__cleanrow(res.group(2)).split()
                    for (dest_state,action_index) in \
                            [ (l[i],l[i+1]) for i in range(0,len(l))[::2] ]:
                        self._transitions[starting_state].append(
                            (int(dest_state)-1,int(action_index)) )

            elif secs[sidx]=="begin state_props": # parse state proposition row
                res=self.__stateproprow.search(l)
                if res:
                    propname=res.group(1).replace('\\"', '"')
                    proplist=[]
                    for propitem in res.group(3).split():
                        try:
                            # single number
                            propnum=int(propitem)-1 # off-by-one
                            proplist.append(propnum)
                        except ValueError:
                            # range of numbers: x..y
                            try:
                                proprange=[int(x) for x in propitem.split("..")]
                            except ValueError:
                                print propitem
                            proprange[0]-=1 # off-by-one
                            proplist.extend(range(*proprange))
                    proplist.sort()
                    self._stateprops[propname]=proplist

            elif secs[sidx]=="begin layout":
                layout_numbers=l.strip().split()
                try:
                    statenum, xcoord, ycoord = [int(x) for x in layout_numbers]
                except ValueError:
                    raise ValueError("Layout section has an illegal row: '%s'" % l.strip())
                statenum-=1
                try:
                    self._layout[statenum]=(xcoord,ycoord)
                except IndexError:
                    raise IndexError("Illegal state number in layout section: %s" % statenum)

            if sidx == len(secs): # we are ready
                break
            else:
                l=file.readline()
                while l.strip()=="":
                    if not l: break
                    l=file.readline()
                if secs[sidx]=="begin state_props" or secs[sidx]=="begin transitions":
                    while (not l.lower().strip() in secs) and (not ";" in l):
                        newline=file.readline()
                        if not newline: break
                        # if there is only one white space in the front of the new row,
                        # delete it... it may be that there should not be white space
                        if l[-3:-1]==".." or newline[:3]==" ..":
                            newline=newline.lstrip()
                        l=l.rstrip()+newline

try:
    import psyco
    psyco.profile()
except: pass

# Compatibility to Python 2.1 requires enumerate:
try:
    enumerate([1])
except:
    def enumerate(list_of_anything):
        i = 0
        result = []
        for a in list_of_anything:
            result.append((i,a))
            i += 1
        return result


if __name__=="__main__":
    """ Testiohjelma """
    class filu:
        def __init__(self):
            self.s=""
        def write(self,s):
            self.s+=s
        def readline(self):
            l=self.s[:self.s.find("\n")+1]
            self.s=self.s[self.s.find("\n")+1:]
            return l

    outf1=filu()
    w=writer(outf1)
    w.set_actionnames(["tau","a","b","c"])
    w.set_transitions([[(0,0),(1,2)],[(0,1),(1,1),(2,3)],[]])
    w.write()

    inf=filu()
    inf.s=outf1.s
    r=reader(inf)
    r.read()

    outf2=filu()
    ww=writer(file=outf2,lsts_object=r)
    # r.__class__=writer
    ww.write(outf2)

    test="Write - read written - rewrite (the written LSTSs should be the same)"
    if outf1.s==outf2.s:
        print "PASS",test
    else:
        print "FAIL",test
        print "-- following LSTS differ:"
        print "---1---"
        print outf1.s
        print "---2--"
        print outf2.s
