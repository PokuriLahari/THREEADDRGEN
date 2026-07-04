import pytest
from lexer import tokenize
from parser import Parser
from ast_nodes import Node

def parse_str(code: str) -> Node:
    tokens = list(tokenize(code))
    parser = Parser(tokens)
    return parser.parse()

def test_simple_addition():
    ast = parse_str("x + 42")
    expected = Node('BINOP', children=[
        Node('IDENTIFIER', attrs={'name': 'x'}),
        Node('INT_LITERAL', attrs={'value': 42})
    ], attrs={'op': '+'})
    assert repr(ast) == repr(expected)

def test_left_associativity():
    ast = parse_str("a - b - c")
    # Expected: ((a - b) - c)
    expected = Node('BINOP', children=[
        Node('BINOP', children=[
            Node('IDENTIFIER', attrs={'name': 'a'}),
            Node('IDENTIFIER', attrs={'name': 'b'})
        ], attrs={'op': '-'}),
        Node('IDENTIFIER', attrs={'name': 'c'})
    ], attrs={'op': '-'})
    assert repr(ast) == repr(expected)

def test_precedence():
    ast1 = parse_str("a + b * c")
    # Expected: (a + (b * c))
    expected1 = Node('BINOP', children=[
        Node('IDENTIFIER', attrs={'name': 'a'}),
        Node('BINOP', children=[
            Node('IDENTIFIER', attrs={'name': 'b'}),
            Node('IDENTIFIER', attrs={'name': 'c'})
        ], attrs={'op': '*'})
    ], attrs={'op': '+'})
    assert repr(ast1) == repr(expected1)

    ast2 = parse_str("a * b + c")
    # Expected: ((a * b) + c)
    expected2 = Node('BINOP', children=[
        Node('BINOP', children=[
            Node('IDENTIFIER', attrs={'name': 'a'}),
            Node('IDENTIFIER', attrs={'name': 'b'})
        ], attrs={'op': '*'}),
        Node('IDENTIFIER', attrs={'name': 'c'})
    ], attrs={'op': '+'})
    assert repr(ast2) == repr(expected2)

def test_parentheses():
    ast = parse_str("(a + b) * c")
    # Expected: ((a + b) * c)
    expected = Node('BINOP', children=[
        Node('BINOP', children=[
            Node('IDENTIFIER', attrs={'name': 'a'}),
            Node('IDENTIFIER', attrs={'name': 'b'})
        ], attrs={'op': '+'}),
        Node('IDENTIFIER', attrs={'name': 'c'})
    ], attrs={'op': '*'})
    assert repr(ast) == repr(expected)

def test_syntax_errors():
    # Empty input
    with pytest.raises(SyntaxError):
        parse_str("")
        
    # Trailing operator
    with pytest.raises(SyntaxError) as excinfo:
        parse_str("a +")
    assert "Expect expression at token" in str(excinfo.value) or "Unexpected token" in str(excinfo.value)

    # Mismatched parentheses
    with pytest.raises(SyntaxError) as excinfo:
        parse_str("(a + b")
    assert "Expect ')'" in str(excinfo.value)

    # Unexpected trailing token
    with pytest.raises(SyntaxError) as excinfo:
        parse_str("a + b c")
    assert "Unexpected token 'c'" in str(excinfo.value)
