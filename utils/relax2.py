#!/usr/bin/env python
#
# fMBT, free Model Based Testing tool
# Copyright (c) 2011, Henri Hansen  henri.hansen@gmail.com
# 
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU Lesser General Public License,
# version 2.1, as published by the Free Software Foundation.
#
# This program is distributed in the hope it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for
# more details.
#
# You should have received a copy of the GNU Lesser General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin St - Fifth Floor, Boston, MA 02110-1301 USA.

import lsts
import sys
DEBUG = True
global i
i=0

try:
    import psyco
    psyco.full()
except:
    pass

class DFA_lsts:
    """ Notes:1. input must be deterministic!!!
              2. all stateprops considered accepting
              3. Initial state must be 0!!! """
    def __init__(self,L=None):
        self.Sigma = []
        self.dist = {}
        if L:
            self.addSigma(L.get_actionnames())
            self.addtrans(L.get_transitions())
            self.addprops(L.get_stateprops())
    def addtrans(self,tr):    
        self.Trans = []
        for i,tl in enumerate(tr):
            self.Trans.append({})
            for (dest,act) in tl:
                if not act in self.Trans[i]:
                    self.Trans[i][act] =set([dest])
                else:
                    self.Trans[i][act].add(dest)                    
    def addprops(self,pr):
        self.acc = set([])
        for p in pr:
            self.acc.update(pr[p])
    def addSigma(self,Sigma):
        if self.Sigma:
            toadd = set(Sigma)
            toadd.difference_update(self.Sigma)
            self.Sigma.extend(list(toadd))
        else:
            self.Sigma = Sigma
    """ Relax is dangerous, unless the DFA is a
        linear execution, as it may run forever.
        Did not bother to implement any weird stuff"""
    def relax(self,s=None,act = None):
        if s in self.acc:
            return set([]) ## nothing is added from accepting states.
        elif not s:
            s = 0
        toadd = set([])
        for a in self.Trans[s]:
            for sp in self.Trans[s][a]:
                toadd.update(self.relax(sp,a))
                toadd.add((sp,a))
        for (sp,a) in toadd:
            if a not in self.Trans[s]:
                self.Trans[s][a] = set([])
            self.Trans[s][a].add(sp)
        return toadd
    """ Returns an LSTS """
    def to_LSTS(self,stream):
        out = lsts.writer(stream)
        out.set_transitions([[(dest,act) for act in s
                              for dest in s[act]] for s in self.Trans])
        out.set_actionnames(self.Sigma)
        prop = {'acc':[i for i in self.acc]}
        for st in self.dist:
            nprop = str(self.dist[st])
            if not nprop in prop:
                prop[nprop] = []
            prop[nprop].append(st)
        out.set_stateprops(prop)
        return out
    """ makes self a full DFA. Again, not safe for
        nondeterministic automaton """
    def t_full(self):
        rej = False
        for t in self.Trans:
            for i in xrange(1,len(self.Sigma)):
                if i in t:continue
                if not rej:
                    rej = len(self.Trans)
                    self.Trans.append({})
                t[i] =set([rej])
        if rej:
            for i in xrange(1,len(self.Sigma)):
                self.Trans[-1][i] = set([rej])
    """cln removes states and trans that cannot reach acc-states."""
    def cln(self):
        revT = [{} for s in self.Trans]
        for s in xrange(len(self.Trans)):
            for a in self.Trans[s]:
                for sp in self.Trans[s][a]:
                    if not a in revT[sp]:
                        revT[sp][a] = set([])
                    revT[sp][a].add(s)
        tag = self.acc.copy()
        Q = list(tag)
        while Q:
            s = Q.pop(0)
            for a in revT[s]:
                for sp in revT[s][a]:
                    if sp in tag:continue
                    tag.add(sp)
                    Q.append(sp)        
        for s in xrange(len(self.Trans)):
            torem = set([])
            for a in self.Trans[s]:
                togo = set([])
                for sp in self.Trans[s][a]:
                    if not sp in tag:
                        togo.add(sp)
                self.Trans[s][a].difference_update(togo)
                if not self.Trans[s][a]:
                    torem.add(a)
            for a in torem:
                self.Trans[s].pop(a)
    """ unreach removes all unreachable states """
    def unreach(self):
        newstates = {0:0}
        trel = [{}]
        cnum = 0
        stack = [0]
        while stack:
            s = stack.pop()
            for a in self.Trans[s]:
                for sp in self.Trans[s][a]:
                    if not sp in newstates:
                        cnum+=1
                        newstates[sp] = cnum
                        trel.append({})
                        stack.append(sp)
                    if not a in trel[newstates[s]]:
                        trel[newstates[s]][a] = set([])
                    trel[newstates[s]][a].add(newstates[sp])
        acc = set([])
        for s in self.acc:
            if s in newstates:
                acc.add(newstates[s])
        self.acc = acc
        self.Trans = trel
    """ backwards, backwadizes """
    def backwards(self):
        trans = [{} for i in xrange(len(self.Trans)+1)]
        for s,t in enumerate(self.Trans):
            for a in self.Trans[s]:
                for sp in self.Trans[s][a]:
                    if not a in trans[sp+1]:
                        trans[sp+1][a] = set([])
                    trans[sp+1][a].add(s+1)
        trans[0][0] = set([s+1 for s in self.acc])
        self.Trans = trans
        self.acc = set([1])
                    
                
    
    """ Min minimizes. Warning: bad and silly.
        It is correct, however. """
    def min(self):
        self.backwards()
        self.remove_taus()
        self.det()
        self.cln()
        self.unreach()
        self.backwards()
        self.remove_taus()
        self.det()
        self.cln()
        self.unreach()

    """ helper method remove_taus removes taus and replaces with
        regular nondeteminism """
    def remove_taus(self):
        init = 0
        foundstates = set([init])
        stack = [init]
        while stack:
            s = stack.pop()
            found2 = set([s])
            stack2 = [s]
            while stack2:
                s2 = stack2.pop()
                if not 0 in self.Trans[s2]:continue
                for s2p in self.Trans[s2][0]:
                    if not s2p in found2:
                        stack2.append(s2p)
                        found2.add(s2p)
                        for a in self.Trans[s2p]:
                            if a == 0:continue
                            if not a in self.Trans[s]:
                                self.Trans[s][a] = set([])                
                            self.Trans[s][a].update(self.Trans[s2p][a])

                               
            for a in self.Trans[s]:
                if a == 0:
                    self.Trans[s][a] = set([])
                    continue
                for sp in self.Trans[s][a]:
                    if sp in foundstates:continue
                    foundstates.add(sp)
                    stack.append(sp)                                         
    """ makes current deterministic.
        warning: may be exponential """
    def det(self):
        init = (0,)
        newstates = {init:0}
        cnum = 0
        stack = [init]
        trel = [{}]
        acc = set([])
        while stack:
            ss = stack.pop()
            for a in xrange(len(self.Sigma)):
                news = set([])
                ac = False
                for s in ss:
                    if a in self.Trans[s]:  
                        for sp in self.Trans[s][a]:
                            news.add(sp)
                            if sp in self.acc:
                                ac = True
                news = list(news)
                news.sort()
                news = tuple(news)
                if not news in newstates:
                    cnum +=1
                    newstates[news] = cnum
                    trel.append({})
                    stack.append(news)
                spp = newstates[news]            
                trel[newstates[ss]][a] = set([spp])
                if ac:acc.add(spp)
        self.Trans = trel
        self.acc = acc

    """ union adds D2, and this is the nondet-
        non-interleaving version """
    def union(self,D2):
        self.addSigma(D2.Sigma)
        cnum = len(self.Trans)
        newstates = {0:0}
        for s in xrange(len(D2.Trans)):
            for a in D2.Sigma:
                ai = D2.Sigma.index(a)
                ni = self.Sigma.index(a)
                if not ai in D2.Trans[s]: continue
                for sp in D2.Trans[s][ai]:
                    if not sp in newstates:
                        self.Trans.append({})
                        newstates[sp] = cnum
                        cnum+=1
                    ss = newstates[s]
                    ssp = newstates[sp]
                    if sp in D2.acc:
                        self.acc.add(ssp)
                    if not ni in self.Trans[ss]:
                        self.Trans[ss][ni] = set([])
                    self.Trans[ss][ni].add(ssp)

        
    """ 'add' adds another trace to current 
        and returns a new DFA. Safe only for det.
        Interleaves them completely """
    def add(self,D2):
        stnumbering = {(0,0):0} # store for the states
        cnumber = 0 # number for the states new DFA
        acc = set([]) # acc-set for the new DFA
        trans = [{}] # transrel for the new. sigma is union.
        stack = [(0,0)] # going in "pseudoDFS"
        Sg1 = self.Sigma
        Sg2 = D2.Sigma
        Sigma = set(Sg1).union(Sg2) # union of alphabets
        Sigma.remove('tau')
        SL = ['tau']
        SL.extend(list(Sigma))
        while stack:
            (x,y) = stack.pop()
            st = stnumbering[(x,y)]            
            if x in self.acc or y in D2.acc: # union
                acc.add(st)
            for a in Sigma:
                ai = SL.index(a)
                if a in Sg1 and a in Sg2: # this is in joint alp.
                    i = self.Sigma.index(a)
                    j = D2.Sigma.index(a)
                    if x == None or not i in self.Trans[x]:
                        Xp = [None]
                    else:
                        Xp = self.Trans[x][i]
                    if y == None or not j in D2.Trans[y]:
                        Yp = [None]
                    else:
                        Yp = D2.Trans[y][j]
                    succ = [(xp,yp) for xp in Xp for yp in Yp]
                    for xp,yp in succ:
                        if not (xp,yp) in stnumbering:
                            cnumber += 1
                            stnumbering[(xp,yp)] = cnumber
                            stack.append((xp,yp))
                            trans.append({})
                        stp = stnumbering[(xp,yp)]
                        if not ai in trans[st]:
                            trans[st][ai] = set([])
                        trans[st][ai].add(stp)
                elif a in Sg1:
                    i = self.Sigma.index(a)
                    if x==None or not i in self.Trans[x]: continue
                    for xp in self.Trans[x][i]:
                        if not (xp,y) in stnumbering:
                            cnumber += 1
                            stnumbering[(xp,y)] = cnumber
                            stack.append((xp,y))
                            trans.append({})
                        stp = stnumbering[(xp,y)]
                        if not ai in trans[st]:
                            trans[st][ai] = set([])
                        trans[st][ai].add(stp)
                elif a in Sg2:
                    j = D2.Sigma.index(a)
                    if y==None or not j in D2.Trans[y]: continue
                    for yp in D2.Trans[y][j]:
                        if not (x,yp) in stnumbering:
                            cnumber += 1
                            stnumbering[(x,yp)] = cnumber
                            stack.append((x,yp))
                            trans.append({})
                        stp = stnumbering[(x,yp)]
                        if not ai in trans[st]:
                            trans[st][ai] = set([])
                        trans[st][ai].add(stp)
        rr = DFA_lsts()
        rr.Trans = trans
        rr.addSigma(SL)
        rr.acc = acc
        return rr
        
    
    """ Intersection calculates the common language. works only
        for det and makes sense only for relaxed versions """
    def intersect(self,D2):
        D2.t_full()
        self.t_full()
        stnumbering = {(0,0):0} # store for the states
        cnumber = 0 # number for the states new DFA
        acc = set([]) # acc-set for the new DFA
        trans = [{}] # transrel for the new. sigma is union.
        stack = [(0,0)] # going in "pseudoDFS"
        Sg1 = set(self.Sigma)
        Sg2 = set(D2.Sigma)
        SigmaU = Sg1.union(Sg2) # union of alphabets
        SigmaU.remove('tau') # We don't consider them.
        SigmaI = Sg1.intersection(Sg2)
        SigmaI.remove('tau')
        SL = ['tau']
        SL.extend(list(SigmaI))
        while stack:
            (x,y) = stack.pop()
            st = stnumbering[(x,y)]            
            if x in self.acc and y in D2.acc: # union
                acc.add(st)
            for a in SigmaU: #NOTE it dismisses taus.               
                if a in SigmaI: # this is in joint alp.
                    ai = SL.index(a)
                    i = self.Sigma.index(a)
                    j = D2.Sigma.index(a)
                    for xp in self.Trans[x][i]:
                        for yp in D2.Trans[y][j]:
                            if not (xp,yp) in stnumbering:
                                cnumber += 1
                                stnumbering[(xp,yp)] = cnumber
                                stack.append((xp,yp))
                                trans.append({})
                            stp = stnumbering[(xp,yp)]
                            if not ai in trans[st]:
                                trans[st][ai] = set([])
                            trans[st][ai].add(stp)
                elif a in Sg1: # here only if in Sg1,not sg2
                    ai = 0 # Noncommon alphabets are replaced by 0
                    i = self.Sigma.index(a)
                    for xp in self.Trans[x][i]:
                        if not (xp,y) in stnumbering:
                            cnumber += 1
                            stnumbering[(xp,y)] = cnumber
                            stack.append((xp,y))
                            trans.append({})
                        stp = stnumbering[(xp,y)]
                        if not ai in trans[st]:
                            trans[st][ai] = set([])
                        trans[st][ai].add(stp)
                elif a in Sg2:
                    ai = 0
                    j = D2.Sigma.index(a)
                    for yp in D2.Trans[y][j]:
                        if not (x,yp) in stnumbering:
                            cnumber += 1
                            stnumbering[(x,yp)] = cnumber
                            stack.append((x,yp))
                            trans.append({})
                        stp = stnumbering[(x,yp)]
                        if not ai in trans[st]:
                            trans[st][ai] = set([])
                        trans[st][ai].add(stp)
        rr = DFA_lsts()
        rr.Trans = trans
        rr.addSigma(SL)
        rr.acc = acc
        rr.remove_taus()
        rr.det()
        rr.cln()
        rr.unreach()
        return rr
    """ retain remoces all the actions except those in 'act'
    """
    def retain(self,act):
        Sigma = act
        trns = [{} for i in self.Trans]
        for s,t in enumerate(self.Trans):
            for a in self.Sigma:
                i = self.Sigma.index(a)
                if a in act:
                    j = Sigma.index(a)
                    trns[s][j] = set([])
                    if i in t:
                        trns[s][j].update(t[i])
                elif i in t:
                    if not 0 in trns[s]:
                        trns[s][0] = set([])
                    trns[s][0].update(t[i])
        self.Trans = trns
        self.Sigma = Sigma
        self.remove_taus()
        self.det()
        self.cln()
        self.unreach()
                
                
    
    """ Negate is a function that takes another dfa,
        and removes from it all accepting traces that
        this one accepts. Result is nondet, in general.
        Not safe otherwise!! """
    def negate(self,D2):
        self.retain(D2.Sigma)        
        if DEBUG:            
            self.to_LSTS(open('foo.lsts','w')).write()
        self.t_full()
        stnumbering = {(0,0):0} # store for the states
        cnumber = 0 # number for the states new DFA
        acc = set([]) # acc-set for the new DFA
        uacc = set([]) # accset of current;used for negating.
        trans = [{}] # transrel for the new. sigma from D2
        stack = [(0,0)] # going in "pseudoDFS"
        while stack:
            (x,y) = stack.pop()
            st = stnumbering[(x,y)]
            if y in D2.acc:
                acc.add(st) # not the final;must be fixed
            if x in self.acc:
                uacc.add(st)
            for a in self.Trans[x]: ## We follow self.
                if self.Sigma[a] in D2.Sigma: # this is in joint alp.
                    b = D2.Sigma.index(self.Sigma[a])
                    for xp in self.Trans[x][a]:
                        if not b in D2.Trans[y]:
                            continue
                        for yp in D2.Trans[y][b]:
                            if not (xp,yp) in stnumbering:
                                cnumber += 1
                                stnumbering[(xp,yp)] = cnumber
                                stack.append((xp,yp))
                                trans.append({})
                            stp = stnumbering[(xp,yp)]
                            if not b in trans[st]:
                                trans[st][b] = set([])
                            trans[st][b].add(stp)
                else: # Others become taus. 
                    for xp in self.Trans[x][a]:
                        if not (xp,y) in stnumbering:
                            cnumber += 1
                            stnumbering[(xp,y)] = cnumber
                            stack.append((xp,y))
                            trans.append({})
                        stp = stnumbering[(xp,y)]
                        if not 0 in trans[st]:
                            trans[st][0] = set([])
                        trans[st][0].add(stp)
        # Now we clean the acc-sets.
     
        acc.difference_update(uacc)
        rr = DFA_lsts()
        rr.Trans = trans
        rr.addSigma(D2.Sigma)
        rr.acc = acc
        rr.remove_taus()
        rr.det()
        return rr
    def addDistances(self):
        ptrans = [{} for st in self.Trans]
        for st in xrange(len(self.Trans)):
            for a in self.Trans[st]:
                for sp in self.Trans[st][a]:
                    if not a in ptrans[sp]:
                        ptrans[sp][a] = set([])
                    ptrans[sp][a].add(st)
        dist = {}
        for st in self.acc:
            found = set([st])
            dist[st] = 0
            Q = [st]
            while Q:
                s = Q.pop(0)
                for a in ptrans[s]:
                    for sp in ptrans[s][a]:
                        if sp in found:
                            continue
                        found.add(sp)
                        if not sp in dist or dist[sp] > dist[s] + 1:
                            dist[sp] = dist[s] + 1
                            Q.append(sp)
        self.dist = dist

class ErrorModel:
    def __init__(self,input_lsts,inst=sys.stdin,outst=sys.stdout):
        if input_lsts: self.A = DFA_lsts(input_lsts)
        else: self.A = None
        self.B = None
        self.inp = inst
        self.out = outst
    def handle_tr(self,tr,N):
        global i
        A = DFA_lsts()
        T = [{}]
        acc = set([])
        cnum = 0
        Sigma = ['tau']
        for name in tr:
            if not name in Sigma:
                Sigma.append(name)
            index = Sigma.index(name)
            T[cnum][index] = set([cnum+1])
            T.append({})
            cnum+=1
        acc.add(cnum)
        A.Trans= T
        A.acc = acc
        A.Sigma = Sigma
        A.relax()
        A.det()
        if N == 'B':
            if not self.A:
                x = Exception('first trace should be an error\n')
            self.A = A.negate(self.A)
        if N == 'A':
            if self.A:
                self.A = self.A.intersect(A)
            else:
                self.A = A
            # reduce from A all (true) prefixes of tr that end with
            # the triggering action tr[-1]
            for index, name in enumerate(tr[:-1]):
                if name == tr[-1]: self.handle_tr(tr[:index+1], 'B')
    def read_tr(self):
        toproc = []
        a = self.inp.readline().rstrip()
        while a:
            if a in ['pass', 'inconclusive']:
                self.handle_tr(toproc,'B')
                toproc = []
            elif a == 'fail':
                self.handle_tr(toproc,'A')
                toproc = []
            else:
                toproc.append(a)
            a = self.inp.readline().rstrip()
                        
    def output(self):
        if self.B and self.A:
            if self.A :
                X = self.B.negate(self.A)
                X.remove_taus()
        elif self.A:
            X = self.A
        else:
            raise Exception('no A-traces, man\n')
        X.min()
        X.addDistances()
        out = X.to_LSTS(self.out)
        out.write()
    def go_online(self):    
        self.read_tr()
        self.output()

if __name__=="__main__":
    if len(sys.argv) > 1:
        input_lsts_file = file(sys.argv[1])
        error_lsts = lsts.reader(input_lsts_file)
    else: error_lsts = None
    X = ErrorModel(error_lsts)
    X.go_online()
