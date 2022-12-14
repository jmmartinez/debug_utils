import typing
import lldb

class SBErrorWrapper(RuntimeError):
    def __init__(self, error : lldb.SBError):
        self.error = error

def visit_breakpoints(debugger: lldb.SBDebugger, breakpoints : typing.Sequence) -> typing.Generator[lldb.SBThread, None, None]:
    debugger.SetAsync(False)
    target : lldb.SBTarget = debugger.GetSelectedTarget()
    if not target.IsValid():
        raise SBErrorWrapper(lldb.SBError("invalid target"))

    target.DeleteAllBreakpoints()

    # create new breakpoints
    for where in breakpoints:
        if isinstance(where, tuple):
            source, line = where
            assert(isinstance(source, str))
            assert(isinstance(line, int))
            breakp = target.BreakpointCreateByLocation(source, line)
        else:
            assert(isinstance(where, str))
            breakp = target.BreakpointCreateByRegex(where)
        print(f"Created breakpoint at {breakp}")

    error = lldb.SBError()
    process : lldb.SBProcess = target.GetProcess()
    if not process or not process.is_alive:
        process = target.Launch(target.GetLaunchInfo(), error)

    # run until the end
    while not error.Fail():
        if not process.is_alive:
            return
        thread : lldb.SBThread = process.GetSelectedThread()
        yield thread
        error = process.Continue()

    raise SBErrorWrapper(error)
