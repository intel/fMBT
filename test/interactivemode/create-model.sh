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

cat > testmodel.aal <<EOF
# preview-depth: 10
aal "interactive_mode_model" {
    language "python" {}

    variables {
        state, model_executed, adapter_executed
    }

    initial_state {
        state = "before-init"
        model_executed = False
        adapter_executed = False
    }

    action "init" {
        guard { return state == "before-init" }
        body {
            state = "initialized"
        }
    }

    action "iReadAllActionsInAdapter" {
        guard { return state == "initialized" }
        body { state = "dead" }
    }

    tag "dead" {
        guard { return state == "dead" }
        action "iStartGoodFmbt" {
            body { state = "alive" }
        }
    }


    tag "alive" {
        guard { return state == "alive" }

        # Quit or terminate fmbt at any time
        action "iQuit", "iTerminate" {
            body {
                state = "dead"
                model_executed = False
                adapter_executed = False
            }
        }

        # Test running some actions on dummy adapters when alive
        action "iExecuteMeOnTheDummy" {}
        action "iAnythingGoesForTheDummy" {}

        # Test that help works always when alive
        action "iHelpEmptyCommand" {}
        action "iHelpUnknownCommand" {}

        # Test action execution at current state.
        action "iNop:ExecuteAtState" {}
        action "iListActionsAtState" {}
        action "iListActionsAtAdapter" {}

        # Test alternative model/adapter execution orders
        action "iExecuteInitAtState" {
            guard { return not (model_executed or adapter_executed) }
            body {
                model_executed = True
                adapter_executed = True
            }
        }

        action "iExecuteInitAtAdapter",
                "iExecuteInitAtAdapterByName" {
            guard { return not adapter_executed }
            body { adapter_executed = True }
        }

        action "iExecuteInitAtAdapterExecModel",
               "iExecuteInitAtStateExecModel" {
            guard { return not model_executed }
            body { model_executed = True }
        }

        action "iExecuteReadAllAtState" {
            guard { return model_executed and adapter_executed }
        }
    }
}
EOF

remote_pyaal --lsts-depth=42 -o testmodel.lsts testmodel.aal
