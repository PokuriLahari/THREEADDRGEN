import tac

def makelist(i: int) -> list[int]:
    """Returns a list containing only the instruction index i."""
    return [i]

def merge(l1: list[int], l2: list[int]) -> list[int]:
    """Concatenates list l1 and list l2."""
    return l1 + l2

def backpatch(lst: list[int], target: int) -> None:
    """Patches the result field of jump quads at instruction indices in lst to target."""
    if hasattr(tac, 'backpatch_log') and lst:
        tac.backpatch_log.append({
            "indices": list(lst),
            "target": target
        })
    for idx in lst:
        if 0 <= idx < len(tac.instructions):
            tac.instructions[idx].result = target
