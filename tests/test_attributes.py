import pytest
from lexer import tokenize
from parser import Parser
from tac import reset_temp, Quad
from attributes import evaluate_attributes
from postfix import to_postfix

def parse_and_eval(code: str):
    reset_temp()
    tokens = list(tokenize(code))
    parser = Parser(tokens)
    ast = parser.parse()
    place, code_quads = evaluate_attributes(ast)
    postfix_str = to_postfix(ast)
    return place, code_quads, postfix_str

def test_simple_eval():
    place, code_quads, postfix_str = parse_and_eval("x + 42")
    assert postfix_str == "x 42 +"
    assert place == "t0"
    assert code_quads == [
        Quad("+", "x", "42", "t0")
    ]

def test_complex_precedence():
    place, code_quads, postfix_str = parse_and_eval("a + b * c - d")
    assert postfix_str == "a b c * + d -"
    assert place == "t2"
    assert code_quads == [
        Quad("*", "b", "c", "t0"),
        Quad("+", "a", "t0", "t1"),
        Quad("-", "t1", "d", "t2")
    ]

def test_parentheses():
    place, code_quads, postfix_str = parse_and_eval("(a + b) * (c - d)")
    assert postfix_str == "a b + c d - *"
    assert place == "t2"
    assert code_quads == [
        Quad("+", "a", "b", "t0"),
        Quad("-", "c", "d", "t1"),
        Quad("*", "t0", "t1", "t2")
    ]

def test_single_leaf():
    place, code_quads, postfix_str = parse_and_eval("42")
    assert postfix_str == "42"
    assert place == "42"
    assert code_quads == []

    place2, code_quads2, postfix_str2 = parse_and_eval("xyz")
    assert postfix_str2 == "xyz"
    assert place2 == "xyz"
    assert code_quads2 == []
