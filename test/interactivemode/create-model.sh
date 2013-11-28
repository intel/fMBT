#!/bin/bash

# fMBT, free Model Based Testing tool
# Copyright (c) 2011, Intel Corporation.
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

GT=../../utils/fmbt-gt
PARALLEL=fmbt-parallel

$GT -o main.lsts '
    P(init0,        p)
    ->
    T(init0,        "init",                       init1)
    T(init1,        "iReadAllActionsInAdapter",   dead)
    
    P(dead,         "dead")
    T(dead,         "iStartGoodFmbt",             alive)
    
    P(alive,        "alive")
    T(alive,        "iQuit",                      dead)
    T(alive,        "iTerminate",                 dead)
'

# Allow running some actions on dummy adapters when alive
$GT -i main.lsts -o main.lsts '
    P(alive,        "alive")
    ->
    P(alive,        "alive")
    T(alive,        "iExecuteMeOnTheDummy",  dummyloop)

    T(dummyloop,    "iAnythingGoesForTheDummy",   alive)
'

# Test that help works always when alive
$GT -i main.lsts -o main.lsts '
    P(alive,        "alive")
    ->
    P(alive,        "alive")
    T(alive,        "iHelpEmptyCommand",          alive)
    T(alive,        "iHelpUnknownCommand",        alive)
'

# Test action execution at current state. Allow quitting from every
# state.
$GT -i main.lsts -o main.lsts '
    P(alive,        "alive")
    ->
    P(alive,        "alive")
    T(alive,        "iNop:ExecuteAtState",        alive)
    T(alive,        "iListActionsAtState",        alive)
    T(alive,        "iListActionsAtAdapter",      alive)
'

$GT -o walk-on-model.lsts '
    P(cannot_walk,  p)
    ->
    P(cannot_walk,  "cannot_walk")
    T(cannot_walk,  "iStartGoodFmbt",             can_walk)

    P(can_walk,     "can_walk")
    T(can_walk,     "iExecuteInitAtState",        initdone)
    T(can_walk,     "iExecuteInitAtAdapter",      adapterdone)
    T(can_walk,     "iExecuteInitAtAdapterByName", adapterdone)
    T(can_walk,     "iExecuteInitAtAdapterExecModel", modeldone)
    T(can_walk,     "iExecuteInitAtStateExecModel", modeldone)

    T(adapterdone,  "iExecuteInitAtStateExecModel", initdone)
    T(adapterdone,  "iExecuteInitAtAdapterExecModel", initdone)

    T(modeldone,    "iExecuteInitAtAdapter",      initdone)

    T(initdone,     "iExecuteReadAllAtState",     actionsread)
' '
    # allow executing iQuit and iTerminate on any state. Cannot walk
    # after them until Fmbt has been restarted.
    P(cannot_walk,  "cannot_walk")
    Q[anystate in S]
    ->
    T(anystate,     "iQuit",                      cannot_walk)
    T(anystate,     "iTerminate",                 cannot_walk)

    P(cannot_walk,  "cannot_walk")
'

$PARALLEL --sync '.*' main.lsts walk-on-model.lsts >testmodel.xrules
