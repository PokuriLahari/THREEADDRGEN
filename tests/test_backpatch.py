import pytest
from lexer import tokenize
from parser import Parser
import tac
from attributes import evaluate_attributes
from postfix import to_postfix

def parse_and_eval(code: str):
    tac.reset_temp()
    tokens = list(tokenize(code))
    parser = Parser(tokens)
    ast = parser.parse()
    evaluate_attributes(ast)
    postfix_str = to_postfix(ast)
    return ast, tac.instructions, postfix_str

def test_boolean_simple_relation():
    ast, instrs, postfix = parse_and_eval("a < b")
    assert postfix == "a b <"
    assert ast.attrs['truelist'] == [0]
    assert ast.attrs['falselist'] == [1]
    assert len(instrs) == 2
    assert str(instrs[0]) == "if a < b goto _"
    assert str(instrs[1]) == "goto _"

def test_boolean_and():
    ast, instrs, postfix = parse_and_eval("a < b && c > d")
    assert postfix == "a b < c d > &&"
    assert ast.attrs['truelist'] == [2]
    assert ast.attrs['falselist'] == [1, 3]
    assert len(instrs) == 4
    # B1's truelist (0) backpatched to M.instr (2)
    assert str(instrs[0]) == "if a < b goto 2"
    assert str(instrs[1]) == "goto _"
    assert str(instrs[2]) == "if c > d goto _"
    assert str(instrs[3]) == "goto _"

def test_boolean_or():
    ast, instrs, postfix = parse_and_eval("a < b || c > d")
    assert postfix == "a b < c d > ||"
    assert ast.attrs['truelist'] == [0, 2]
    assert ast.attrs['falselist'] == [3]
    assert len(instrs) == 4
    # B1's falselist (1) backpatched to M.instr (2)
    assert str(instrs[0]) == "if a < b goto _"
    assert str(instrs[1]) == "goto 2"
    assert str(instrs[2]) == "if c > d goto _"
    assert str(instrs[3]) == "goto _"

def test_boolean_not():
    ast, instrs, postfix = parse_and_eval("!(a < b)")
    assert postfix == "a b < !"
    # Truelist/falselist swapped
    assert ast.attrs['truelist'] == [1]
    assert ast.attrs['falselist'] == [0]

def test_boolean_literals():
    ast, instrs, postfix = parse_and_eval("true && false")
    assert postfix == "true false &&"
    # true emits "goto None" at index 0 (truelist=[0])
    # false emits "goto None" at index 1 (falselist=[1])
    # true's truelist backpatched to 1
    assert ast.attrs['truelist'] == []
    assert ast.attrs['falselist'] == [1]
    assert len(instrs) == 2
    assert str(instrs[0]) == "goto 1"
    assert str(instrs[1]) == "goto _"

def test_boolean_complex_nesting():
    # (a < b || c > d) && e == f
    ast, instrs, postfix = parse_and_eval("(a < b || c > d) && e == f")
    assert postfix == "a b < c d > || e f == &&"
    # Let's check instructions:
    # 0: if a < b goto _ (truelist=[0])
    # 1: goto 2         (falselist=[1] backpatched to 2)
    # 2: if c > d goto _ (truelist=[2])
    # 3: goto _         (falselist=[3])
    # (B1 || B2) truelist = [0, 2], falselist = [3]
    # Then we have && e == f (which starts at 4)
    # So (B1 || B2) truelist is backpatched to 4
    # 4: if e == f goto _ (truelist=[4])
    # 5: goto _         (falselist=[5])
    # Result truelist = [4]
    # Result falselist = merge([3], [5]) = [3, 5]
    assert ast.attrs['truelist'] == [4]
    assert ast.attrs['falselist'] == [3, 5]
    
    assert str(instrs[0]) == "if a < b goto 4"
    assert str(instrs[1]) == "goto 2"
    assert str(instrs[2]) == "if c > d goto 4"
    assert str(instrs[3]) == "goto _"
    assert str(instrs[4]) == "if e == f goto _"
    assert str(instrs[5]) == "goto _"
