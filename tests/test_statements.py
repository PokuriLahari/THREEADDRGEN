import pytest
from lexer import tokenize
from parser import Parser
import tac
from attributes import evaluate_attributes

def parse_and_eval_stmt(code: str):
    tac.reset_temp()
    tokens = list(tokenize(code))
    parser = Parser(tokens)
    ast = parser.parse()
    evaluate_attributes(ast)
    if 'next' in ast.attrs:
        from backpatch import backpatch
        backpatch(ast.attrs['next'], tac.nextinstr())
    return ast, tac.instructions

def test_single_assignment():
    ast, instrs = parse_and_eval_stmt("c = 5;")
    assert ast.kind == 'STMT_LIST'
    assert len(ast.children) == 1
    assert ast.children[0].kind == 'ASSIGN_STMT'
    assert ast.attrs['next'] == []
    assert len(instrs) == 1
    assert str(instrs[0]) == "c = 5"

def test_if_no_else():
    ast, instrs = parse_and_eval_stmt("if (a < b) c = 1;")
    assert ast.kind == 'STMT_LIST'
    if_node = ast.children[0]
    assert if_node.kind == 'IF_STMT'
    
    # 0: if a < b goto 2
    # 1: goto 3
    # 2: c = 1
    assert len(instrs) == 3
    assert str(instrs[0]) == "if a < b goto 2"
    assert str(instrs[1]) == "goto 3"
    assert str(instrs[2]) == "c = 1"
    
    # B.falselist is [1]. S1.next is [].
    # So S.next (IF_STMT.attrs['next']) is [1]
    assert if_node.attrs['next'] == [1]

def test_if_else():
    ast, instrs = parse_and_eval_stmt("if (a < b) { c = 1; } else { c = 2; }")
    assert ast.kind == 'STMT_LIST'
    if_else_node = ast.children[0]
    assert if_else_node.kind == 'IF_ELSE_STMT'
    
    # 0: if a < b goto 2
    # 1: goto 4
    # 2: c = 1
    # 3: goto 5
    # 4: c = 2
    assert len(instrs) == 5
    assert str(instrs[0]) == "if a < b goto 2"
    assert str(instrs[1]) == "goto 4"
    assert str(instrs[2]) == "c = 1"
    assert str(instrs[3]) == "goto 5"
    assert str(instrs[4]) == "c = 2"
    
    assert if_else_node.attrs['next'] == [3]

def test_statement_sequencing():
    ast, instrs = parse_and_eval_stmt("{ x = 10; y = 20; }")
    assert ast.kind == 'STMT_LIST'
    # Block returns the inner STMT_LIST
    assert len(ast.children) == 1
    inner_list = ast.children[0]
    assert inner_list.kind == 'STMT_LIST'
    assert len(inner_list.children) == 2
    
    assert len(instrs) == 2
    assert str(instrs[0]) == "x = 10"
    assert str(instrs[1]) == "y = 20"
    assert inner_list.attrs['next'] == []

def test_while_loop():
    ast, instrs = parse_and_eval_stmt("while (a < b) c = c + 1;")
    assert ast.kind == 'STMT_LIST'
    while_node = ast.children[0]
    assert while_node.kind == 'WHILE_STMT'
    
    # 0: if a < b goto 2
    # 1: goto 5
    # 2: t0 = c + 1
    # 3: c = t0
    # 4: goto 0
    assert len(instrs) == 5
    assert str(instrs[0]) == "if a < b goto 2"
    assert str(instrs[1]) == "goto 5"
    assert str(instrs[2]) == "t0 = c + 1"
    assert str(instrs[3]) == "c = t0"
    assert str(instrs[4]) == "goto 0"
    
    assert while_node.attrs['next'] == [1]

def test_while_loop_with_braces():
    ast, instrs = parse_and_eval_stmt("while (i < n) { i = i + 1; }")
    assert ast.kind == 'STMT_LIST'
    while_node = ast.children[0]
    assert while_node.kind == 'WHILE_STMT'
    
    # 0: if i < n goto 2
    # 1: goto 5
    # 2: t0 = i + 1
    # 3: i = t0
    # 4: goto 0
    assert len(instrs) == 5
    assert str(instrs[0]) == "if i < n goto 2"
    assert str(instrs[1]) == "goto 5"
    assert str(instrs[2]) == "t0 = i + 1"
    assert str(instrs[3]) == "i = t0"
    assert str(instrs[4]) == "goto 0"
    
    assert while_node.attrs['next'] == [1]

def test_complex_mixed_program():
    code = """
    i = 0;
    while (i < n) {
        if (i < 5) {
            x = x + 1;
        } else {
            x = x + 2;
        }
        i = i + 1;
    }
    """
    ast, instrs = parse_and_eval_stmt(code)
    # Check that no jump destination is unpatched (no "_" present in instructions)
    for i, inst in enumerate(instrs):
        assert "_" not in str(inst), f"Unpatched jump at instruction {i}: {inst}"

def test_statement_postfix():
    from postfix import to_postfix
    # Test simple assignment postfix
    tokens = list(tokenize("a = b + c * d;"))
    parser = Parser(tokens)
    ast = parser.parse()
    assert to_postfix(ast) == "a b c d * + ="

    # Test conditional statement postfix
    tokens = list(tokenize("if (a < b) c = 1; else c = 2;"))
    parser = Parser(tokens)
    ast = parser.parse()
    # Note: LBRACE parser rules return a STMT_LIST. 
    # Here the single statements are returned.
    # a < b c 1 = c 2 = ifelse
    assert to_postfix(ast) == "a b < c 1 = c 2 = ifelse"

def test_visualization():
    import os
    from visualizer import visualize_ast
    
    tokens = list(tokenize("a = b + 1;"))
    parser = Parser(tokens)
    ast = parser.parse()
    evaluate_attributes(ast)
    
    filename = "test_output"
    svg_str = visualize_ast(ast, filename)
    
    assert isinstance(svg_str, str)
    assert "<svg" in svg_str
    assert "</svg>" in svg_str
    
    svg_path = f"{filename}.svg"
    assert os.path.exists(svg_path)
    os.remove(svg_path)



