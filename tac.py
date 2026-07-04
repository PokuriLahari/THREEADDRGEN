_temp_counter = 0
instructions = []
emitted_history = []
backpatch_log = []

class Quad:
    """Represents a Three Address Code (TAC) Quad: result = arg1 op arg2."""
    def __init__(self, op: str, arg1: str, arg2: str, result: str):
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2
        self.result = result  # result serves as the target index for jump quads

    def copy(self):
        """Creates a duplicate of this Quad."""
        return Quad(self.op, self.arg1, self.arg2, self.result)

    def __str__(self) -> str:
        target_str = str(self.result) if self.result is not None else "_"
        if self.op == 'goto':
            return f"goto {target_str}"
        elif self.op.startswith('if'):
            relop = self.op[2:]
            return f"if {self.arg1} {relop} {self.arg2} goto {target_str}"
        elif self.op == '=':
            return f"{self.result} = {self.arg1}"
        return f"{self.result} = {self.arg1} {self.op} {self.arg2}"

    def __repr__(self) -> str:
        return f"Quad({self.op!r}, {self.arg1!r}, {self.arg2!r}, {self.result!r})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Quad):
            return NotImplemented
        return (self.op == other.op and 
                self.arg1 == other.arg1 and 
                self.arg2 == other.arg2 and 
                self.result == other.result)

def reset_temp():
    """Resets the temporary variable counter to 0 and clears emitted instructions."""
    global _temp_counter, instructions, emitted_history, backpatch_log
    _temp_counter = 0
    instructions = []
    emitted_history = []
    backpatch_log = []

def nextinstr() -> int:
    """Returns the index of the next instruction to be emitted."""
    return len(instructions)

def newtemp() -> str:
    """Generates a new unique temporary variable name, e.g., t0, t1, ..."""
    global _temp_counter
    name = f"t{_temp_counter}"
    _temp_counter += 1
    return name

def emit(op: str, arg1: str, arg2: str, result: str) -> Quad:
    """Emits and returns a new TAC Quad, appending it to the global list."""
    quad = Quad(op, arg1, arg2, result)
    instructions.append(quad)
    emitted_history.append(quad.copy())
    return quad


