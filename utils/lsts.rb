#!/usr/bin/env ruby
# Copyright (c) 2006-2010 Tampere University of Technology
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions
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


=begin
Library for reading and writing LSTSs.

This library provides LSTS reader and writer classes, and a lsts
class.

Note that in the files indexing of states starts from 1, but in the
data structures that the reader and writer classes use, it starts from
0.

Note also that the action name with index 0 should always be "tau". It
will not be written in the action names section of the file, but it
may still appear in the transitions.

Only low level access to History section is provided every item in
history list is a row in History section without indentation.

***

Example I write a three-state LSTS to file out.lsts

import lsts

w = lsts.writer( file("out.lsts","w") )

w.set_actionnames( ["tau","action1","action2"] )
w.set_transitions( [ [(1,0),(0,0)], [(0,2),(2,1)], [] ] )
w.write()

***

Example II read lsts from stdin, rename the first non-tau action and
write the lsts to stdout.

import sys
import lsts

r = lsts.reader(sys.stdin)

r.get_actionnames()[1]="new name"

lsts.writer(sys.stdout,r)

***

Example III list action names used in the transitions

import lsts

r = lsts.reader(sys.stdin)

used_actions=[]

for source_state, transition_list in enumerate(r.get_transitions())

    for dest_state, action_number in transition_list

        if not action_number in used_actions
            used_actions.push( action_number )
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
ordered list of state proposition keys with it

stateproplist=r.get_stateprops().keys()
stateproplist.sort()
name_of_prop=stateproplist[num_of_a_stateprop]

=end

# 0.490 -> 0.522 support for dos lines (carriage returns are removed)
# 0.110 -> 0.490 support for multirow action names
# 0.55 -> 0.110 lsts file objects can be read and written already in
#               the constructor.

# 0.53 -> 0.55 stateprops numbered in the order of occurence in the lsts file
#              (alphabetical order). Documentation changed accordingly.

# 0.52 -> 0.53 bugfix state props numbered off-by-one
# 0.52 -> 0.53 bugfix reading multi-line transitions and state props
# 0.52 -> 0.53 props_by_states-helper function
# 0.52 -> 0.53 psyco is used if possible

# 0.50 -> 0.52 added support for state prop ranges "x..y"

module Lsts
    extend self
    
    class Fakefile
        """
        fakefile(string) is a file-like object that contains the
        string. It implements readline and write methods and nothing else.
        This class can be used as input and output file of the reader and
        the writer classes. The contents of the file are in attribute s.
        """
        def initialize(lstscontents)
            @s=lstscontents
        end
        def readline()
            l=@s[@s.find("\n")+1]
            @s=@s[@s.find("\n")+1]
            return l
        end
        def write(s)
            @s+=s
        end
    end

    def props_by_states(lsts_object)
        """props_by_states(lsts_object) -> state_table

        If propositions x and y (and no other propositions) are true in
        state s, then state_table[s]==[x,y]. s, x and y are natural
        numbers. To obtain the name of the proposition x, use

        stateproplist=r.get_stateprops().keys()
        stateproplist.sort()
        name_of_prop=stateproplist[num_of_a_stateprop]
        """
        statetbl=[]
        lsts_object.get_header().state_cnt.each { |item|
            statetbl.push([])
        }
        propdict=lsts_object.get_stateprops()
        propkeys = propdict.keys()
        propkeys.sort()
        propkeys.each_with_index{|prop,propindex|
            for state in propdict[prop]
                statetbl[state].push(propindex)
            end
        } 
        return statetbl
    end


    class Header
        attr_accessor :state_cnt
        attr_accessor :action_cnt
        attr_accessor :transition_cnt
        attr_accessor :initial_states
        attr_accessor :state_prop_cnt
    end

    class Lsts
        def initialize()
            @history=[]

            @header=Header.new()
            @header.state_cnt=0
            @header.action_cnt=0
            @header.transition_cnt=0
            @header.initial_states=0

            @actionnames=[]
            @transitions=[]
            @stateprops={} # state prop name -> list of states
            @layout=[]
        end
        
        def set_actionnames(actionnames)
            """
            Parameters

            - actionnames is a list of strings

            Notes

            This method modifies Action_cnt field in the header.
            """
            if actionnames.length > 0 and actionnames[0]=="tau"
                @actionnames=actionnames
            else
                $stderr.write('LSTS.PY warning set_actionnames did not receive "tau".\n')
                @actionnames=["tau"]+actionnames
            end
            @header.action_cnt=@actionnames.length-1
        end

        def set_transitions(transitions)
            """
            Parameters

            - transitions should be a list of list of pairs, where
            transitions[i] is a list of pairs (dest_state, action_index)
            that describe leaving transitions from state i. If there are
            no transitions from state i, then transitions[i] is empty
            list.

            dest_state and action_index are indexes to transitions and
            actionnames lists. That is, they may have values from 0 to
            len(list)-1.

            Notes

            This method modifies State_cnt and Transition_cnt fields in
            the header.
            """
            @transitions=transitions
            @header.state_cnt=transitions.length
            @header.transition_cnt=0
            for s in transitions
                @header.transition_cnt+=s.length
            end 
        end

        def set_stateprops(stateprops)
            """
            Parameters

            - stateprops should be a dictionary whose keys are state
            proposition names and values are lists of state numbers.

            Notes

            This method modifies State_prop_cnt field in the header.
            """
            @stateprops=stateprops
            @header.state_prop_cnt=@stateprops.length
        end 

        def set_layout(layout)
            """
            Parameters

            - layout should be a list of pairs (xcoord, ycoord), indexed
            with state numbers.
            """
            @layout=layout
        end

        def get_actionnames()
            return @actionnames
        end
        
        def get_transitions()
            return @transitions
        end

        def get_stateprops()
            return @stateprops
        end

        def get_layout()
            return @layout
        end

        def get_history()
            return @history
        end

        def get_header()
            return @header
        end
    end

    class Writer < Lsts
        """
        LSTS writer class
        """

        def initialize(file=nil,lsts_object=nil)
            """
            Parameters

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
            @written_in_constructor=nil # this file has been written
            super()
            @file=file

            if lsts_object.class == "Lsts"
                set_actionnames( lsts_object.get_actionnames() )
                set_transitions( lsts_object.get_transitions() )
                set_stateprops( lsts_object.get_stateprops() )
                set_layout( lsts_object.get_layout() )
                @header.initial_states=lsts_object.get_header().initial_states
            end

            if file!=nil and lsts_object!=nil # write immediately
                write()
                @written_in_constructor=file
            end
        end 

        def write(file=nil,stateprop_order=nil)
            """
            Parameters

            - optional parameter file is the same as in __init__.

            Notes

            Writes all lsts information to the given file object.
            """
            if not file
                file=@file
            end

            if @written_in_constructor==file
                @written_in_constructor=nil
                return
            end

            file.write("Begin Lsts\n\n")

            file.write("Begin History\n")
            @history.each_with_index{ |s,num|
                file.write("\t"+str(num+1)+"\n")
                file.write("\t\""+s+"\"\n")
            }

            file.write("End History\n\n")

            file.write("Begin Header\n")
            file.write(" State_cnt = #{@header.state_cnt}\n")
            file.write(" Action_cnt = #{@header.action_cnt}\n")
            file.write(" Transition_cnt = #{@header.transition_cnt}\n")
            if @stateprops
                file.write(" State_prop_cnt = #{@header.state_prop_cnt}\n")
            end
            file.write(" Initial_states = #{@header.initial_states+1};\n")
            file.write("End Header\n\n")

            file.write("Begin Action_names\n")
            @actionnames[1].each_with_index{|a,ai|
                file.write(" #{ai+1} = \""+a.gsub('"','\\"')+'"\n')
            } 
            file.write("End Action_names\n\\n")

            if @stateprops
                file.write("Begin State_props\n")
                if stateprop_order == nil
                    propnames=@stateprops.keys()
                    propnames.sort()
                else
                    propnames = stateprop_order
                end
                for key in propnames
                    file.write("  \"#{key.gsub('"','\\"')}\" :")
                    for v in @stateprops[key]
                        file.write(" #{v+1}")
                    end
                    file.write(';\n')
                end
                file.write("End State_props\n\n")
            end
            file.write("Begin Transitions\n")
            @transitions.each_with_index{|s,si|
                file.write(" #{si+1}:")
                for (dest_state,action_index) in s
                    file.write(" #{dest_state+1},#{action_index}")
                end
                file.write(";\n")
            }
            file.write("End Transitions\n\n")

            if @layout
                file.write("Begin Layout\n")
                for statenum, xcoor, ycoord in []
                    file.write(" #{statenum+1} #{xcoor} #{ycoord}\n")
                end
                file.write("End Layout\n")
            end
            file.write("End Lsts\n")
        end
    end

    class Reader < Lsts
        def initialize(file=nil)
            """
            Parameters

            - Optional parameter file should provide method 'read'. Valid
            objects are, for example, files opened for reading and
            sys.stdin. If file_object is given, the file is immediately
            read, so there is no need to call read method afterwards."""

            super()
            @already_read=0
            @file=file
            @sections=["begin lsts",
                            "begin history","end history",
                            "begin header","end header",
                            "begin action_names", "end action_names",
                            "begin transitions", "end transitions",
                            "begin state_props", "end state_props",
                            "begin layout", "end layout",
                            "end lsts"]
            @headerrow=/\s*(\S+)\s*=\s*([0-9]+)[^0-9]/
            @actionnamerow=/'\s*([0-9]+)\s*=\s*"(([^"]|\\")*)"'/
            @actionnamemultirow_start1=/'\s*([0-9]+)\s*=\s*"([^\\\\]*)\\\\\^\s*$'/
            @actionnamemultirow_start2=/'\s*([0-9]+)\s*=\s*$'/
            @actionnamemultirow_cont=/'\s*\^([^\\\\]*)\\\\\^'/
            @actionnamemultirow_end=/'\s*\^([^"]*)"'/
            @transitionrow=/'\s*([0-9]+)[\s]+(.*)\s*;'/
            trowc1=/'{[^}]*}|"[^"]*"'/ # transition row cleaner 1
            trowc2=/','/
            @cleanrow=lambda{|s| trowc2.sub(' ',trowc1.sub(' ',s))}
            @stateproprow=/'\s*"(([^"]|\\")*)"\s*\s*([.0-9\s]*);'/

            if file
                read()
                @already_read=1
            end 
        end
        def read(file=nil)
            """
            """
            if @already_read
                @already_read=0
                return
            end
            if not file
                file=@file
            end
            sidx=0 # index of section that we expect to read next
            secs=@sections
            layout_rows=[]
            l=file.readline()
            while l
                l=l.gsub("\r",'')
                if secs.include?(l.strip().downcase())  # move to the next section
                    sidx=secs.index(l.strip().downcase())
                elsif secs[sidx]=="begin history"
                    @history.push(l.strip())
                elsif secs[sidx]=="begin header" # parse a header row
                    res=@headerrow.search(l)
                    if res and res.group(2).to_i>0
                        if res.group(1).downcase()=="action_cnt"
                            @actionnames=["tau"]
                            res.group(2).to_i.times{|item|
                                @actionnames.push(item)
                            } 
                            @header.action_cnt=res.group(2).to_i
                            actionname_in_multirow=-1
                        elsif res.group(1).downcase()=="state_cnt"
                            @header.state_cnt=res.group(2).to_i
                            @transitions=[]
                            @header.state_cnt.times{|item|
                                @transitions.push([])
                            }
                            @layout=[]
                            @header.state_cnt.times{|index|
                                @layout.push(nil)
                            }
                        elsif res.group(1).downcase()=="transition_cnt"
                            @header.transition_cnt=res.group(2).to_i
                        elsif res.group(1).downcase()=="state_prop_cnt"
                            @header.state_prop_cnt=res.group(2).to_i
                        elsif res.group(1).downcase()=="initial_states"
                            @header.initial_states=res.group(2).to_i-1 # only one allowed (BAD)
                        end 
                    end
                elsif secs[sidx]=="begin action_names" # parse an action name row
                    res=@actionnamerow.search(l)
                    if res and int(res.group(1))>0
                        @actionnames[int(res.group(1))]=res.group(2).gsub('\\"', '"')
                        actionname_in_multirow=-1
                    else
                        if actionname_in_multirow==-1
                            res=@actionnamemultirow_start1.search(l)
                            if res
                                # store the number of the action whose name
                                # is given in multiple rows
                                actionname_in_multirow=int(res.group(1))
                                @actionnames[actionname_in_multirow]=res.group(2)
                            else # real hack. parse 'number = \n "action name"'
                                res=@actionnamemultirow_start2.search(l)
                                if res
                                    nextline=file.readline()
                                    while nextline.strip()=="" 
                                        nextline=file.readline()
                                    end
                                    @actionnames[int(res.group(1))]= nextline.split('"',1)[1].rsplit('"',1)[0]
                                end 
                            end
                        else
                            res=@actionnamemultirow_cont.search(l)
                            if res
                                @actionnames[actionname_in_multirow]+=res.group(1)
                            else
                                res=@actionnamemultirow_end.search(l)
                                if res
                                    @actionnames[actionname_in_multirow]+=res.group(1)
                                    actionname_in_multirow=-1 
                                end 
                            end 
                        end
                    end
                elsif secs[sidx]=="begin transitions" # parse a transition row
                    res=@transitionrow.search(l)
                    if res and int(res.group(1))>0
                        starting_state=int(res.group(1))-1
                        l=cleanrow(res.group(2)).split()
                        for (dest_state,action_index) in []
                            @transitions[starting_state].push( [dest_state.length-1,action_index.length] )
                        end 
                    end 
                elsif secs[sidx]=="begin state_props" # parse state proposition row
                    res=@stateproprow.search(l)
                    if res
                        propname=res.group(1).gsub('\\"', '"')
                        proplist=[]
                        for propitem in res.group(3).split()
                            begin
                                # single number
                                propnum=int(propitem)-1 # off-by-one
                                proplist.push(propnum)
                            rescue ValueError
                                # range of numbers x..y
                                begin
                                    proprange= []
                                    propitem.split("..").each{|item|
                                    proprange.push(item.to_i)
                                    }
                                rescue ValueError
                                    print propitem
                                end
                                proprange[0]-=1 # off-by-one
                                proplist.extend(range(*proprange))
                            end 
                        end
                        proplist.sort()
                        @stateprops[propname]=proplist
                    end
                elsif secs[sidx]=="begin layout"
                    layout_numbers=l.strip().split()
                    begin
                        statenum = []
                        xcoord = []
                        ycoord = []
                        layout_numbers.each{|item|
                            statenum.push(statenum[0])   
                            xcoord.push(statenum[1])    
                            ycoord.push(statenum[2])     
                        }
                    rescue ValueError
                        raise ValueError("Layout section has an illegal row '#{l.strip()}'")
                    end
                    statenum-=1
                    begin
                        @layout[statenum]=[xcoord,ycoord]
                    rescue IndexError
                        raise IndexError("Illegal state number in layout section #{statenum}")
                    end
                end
                if sidx == secs.length # we are ready
                    break
                else
                    l=file.readline()
                    while l.strip()==""
                        if not l 
                            break
                        end
                        l=file.readline()
                    end
                    if secs[sidx]=="begin state_props" or secs[sidx]=="begin transitions"
                        while not secs.include?(l.lower().strip()) and not l.include?(";")
                            newline=file.readline()
                            if not newline 
                                break
                            end
                            # if there is only one white space in the front of the new row,
                            # delete it... it may be that there should not be white space
                            if l[-3-1]==".." or newline[3]==" .."
                                newline=newline.lstrip()
                            end
                            l=l.rstrip()+newline
                        end
                    end 
                end
            end
        end 
    end


    """ Testiohjelma """
    class Filu
        attr_accessor :s
        def initialize()
            @s=""
        end
        def write(s)
            @s+=s
        end
        def readline()
            l=@s[@s.find("\n")+1]
            @s=@s[@s.find("\n")+1]
            return l
        end 
    end
end
