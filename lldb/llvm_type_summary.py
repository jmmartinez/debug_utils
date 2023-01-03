# load commands with
#   $ lldb --one-line "command script import llvm_type_summary.py"

import lldb, sys

def summary_from_dump(value: lldb.SBValue, internal_dict : dict):
    value.EvaluateExpression("llvm::dbgs().SetBuffered()")
    value.EvaluateExpression("this->dump()")
    StringStart = value.EvaluateExpression("llvm::dbgs().OutBufStart").unsigned
    StringEnd = value.EvaluateExpression("llvm::dbgs().OutBufCur").unsigned
    StringSize = StringEnd - StringStart
    if not StringSize:
        return value.summary

    error = lldb.SBError()
    process : lldb.SBProcess = value.GetProcess()
    dump_output = process.ReadCStringFromMemory(StringStart, StringEnd - StringStart, error)
    if not error.Success():
        raise Exception(f"error: {error}")

    value.EvaluateExpression("llvm::dbgs().OutBufCur = llvm::dbgs().OutBufStart")
    value.EvaluateExpression("llvm::dbgs().SetUnbuffered()")

    return dump_output 

CATEGORY = "llvm"
TYPES = { 
  "llvm::Instruction" : summary_from_dump,
  "llvm::SDNode" : summary_from_dump,
}

# load with "type summary add <type> --python-function"
def __lldb_init_module(debugger : lldb.SBDebugger, internal_dict : dict):
    for llvm_type, callback in TYPES.items():
        debugger.HandleCommand(f"type summary add --category {CATEGORY} -P {llvm_type} -F {__name__}.{callback.__name__}")
    debugger.HandleCommand(f"type category enable {CATEGORY}")
