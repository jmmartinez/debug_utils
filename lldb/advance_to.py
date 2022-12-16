from argparse import ArgumentParser
from shlex import split as split_args
from itertools import chain

import lldb, lldb_utils

# load module with
#   $ lldb --one-line "command script import advance_to.py"
# then do
#   > advance_to_condition --at "PersonDatabase.cpp:100" --cond "Person->age == -1"

@lldb.command()
def advance_to_condition(
    debugger : lldb.SBDebugger,
    command : str,
    result : lldb.SBCommandReturnObject,
    _ : dict):
    """Advance to the first breakpoint where the condition is met"""

    parser = ArgumentParser(prog=__name__, description=__doc__)
    parser.add_argument("--at", nargs="+", action="append", help="Breakpoint to stop and execute condition", required=True)
    parser.add_argument("--cond", type=str, help="Condition to execute at breakpoint", required=True)
    args = parser.parse_args(split_args(command))

    breakpoints = []
    for breakpoint_loc in chain(*args.at):
        try:
            source, line = breakpoint_loc.split(":")
            breakpoints.append((source, int(line)))
        except _:
            breakpoints.append(breakpoint_loc)

    condition : str = args.cond

    # run until the end
    try:
        for thread in lldb_utils.visit_breakpoints(debugger, breakpoints):
            frame : lldb.SBFrame = thread.frame[0]
            condition_evaluates_to_true = frame.EvaluateExpression(condition).unsigned != 0
            if not condition_evaluates_to_true:
                continue

            print(f"Stopped at {frame}: condition {condition} evaluated to true")

            # give back control to the user
            return

    except lldb_utils.SBErrorWrapper as error:
        result.SetError(error.error)

    return
