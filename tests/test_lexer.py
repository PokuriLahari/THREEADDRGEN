import pytest
from lexer import tokenize, Token

def test_assignment():
    code = "x = 42;"
    tokens = list(tokenize(code))
    expected = [
        Token("IDENTIFIER", "x", 1),
        Token("ASSIGN", "=", 1),
        Token("INT_LITERAL", "42", 1),
        Token("SEMICOLON", ";", 1)
    ]
    assert tokens == expected

def test_if_else():
    code = (
        "if (x == 1) {\n"
        "    y = 2;\n"
        "} else {\n"
        "    y = 3;\n"
        "}"
    )
    tokens = list(tokenize(code))
    expected = [
        Token("IF", "if", 1),
        Token("LPAREN", "(", 1),
        Token("IDENTIFIER", "x", 1),
        Token("EQ", "==", 1),
        Token("INT_LITERAL", "1", 1),
        Token("RPAREN", ")", 1),
        Token("LBRACE", "{", 1),
        Token("IDENTIFIER", "y", 2),
        Token("ASSIGN", "=", 2),
        Token("INT_LITERAL", "2", 2),
        Token("SEMICOLON", ";", 2),
        Token("RBRACE", "}", 3),
        Token("ELSE", "else", 3),
        Token("LBRACE", "{", 3),
        Token("IDENTIFIER", "y", 4),
        Token("ASSIGN", "=", 4),
        Token("INT_LITERAL", "3", 4),
        Token("SEMICOLON", ";", 4),
        Token("RBRACE", "}", 5),
    ]
    assert tokens == expected

def test_while_loop():
    code = (
        "while (count < 10) {\n"
        "    count = count + 1;\n"
        "}"
    )
    tokens = list(tokenize(code))
    expected = [
        Token("WHILE", "while", 1),
        Token("LPAREN", "(", 1),
        Token("IDENTIFIER", "count", 1),
        Token("LT", "<", 1),
        Token("INT_LITERAL", "10", 1),
        Token("RPAREN", ")", 1),
        Token("LBRACE", "{", 1),
        Token("IDENTIFIER", "count", 2),
        Token("ASSIGN", "=", 2),
        Token("IDENTIFIER", "count", 2),
        Token("PLUS", "+", 2),
        Token("INT_LITERAL", "1", 2),
        Token("SEMICOLON", ";", 2),
        Token("RBRACE", "}", 3),
    ]
    assert tokens == expected

def test_boolean_expression():
    code = "bool_val = true && false || !flag;"
    tokens = list(tokenize(code))
    expected = [
        Token("IDENTIFIER", "bool_val", 1),
        Token("ASSIGN", "=", 1),
        Token("TRUE", "true", 1),
        Token("AND", "&&", 1),
        Token("FALSE", "false", 1),
        Token("OR", "||", 1),
        Token("NOT", "!", 1),
        Token("IDENTIFIER", "flag", 1),
        Token("SEMICOLON", ";", 1)
    ]
    assert tokens == expected

def test_comments_and_whitespace():
    code = (
        "// Single line comment\n"
        "x = 1; /* Multi-line\n"
        "comment */ y = 2;"
    )
    tokens = list(tokenize(code))
    expected = [
        Token("IDENTIFIER", "x", 2),
        Token("ASSIGN", "=", 2),
        Token("INT_LITERAL", "1", 2),
        Token("SEMICOLON", ";", 2),
        Token("IDENTIFIER", "y", 3),
        Token("ASSIGN", "=", 3),
        Token("INT_LITERAL", "2", 3),
        Token("SEMICOLON", ";", 3)
    ]
    assert tokens == expected

def test_operators_all():
    code = "+ - * / = == != < > <= >= && || !"
    tokens = list(tokenize(code))
    expected = [
        Token("PLUS", "+", 1),
        Token("MINUS", "-", 1),
        Token("TIMES", "*", 1),
        Token("DIVIDE", "/", 1),
        Token("ASSIGN", "=", 1),
        Token("EQ", "==", 1),
        Token("NE", "!=", 1),
        Token("LT", "<", 1),
        Token("GT", ">", 1),
        Token("LE", "<=", 1),
        Token("GE", ">=", 1),
        Token("AND", "&&", 1),
        Token("OR", "||", 1),
        Token("NOT", "!", 1),
    ]
    assert tokens == expected

def test_invalid_character():
    with pytest.raises(SyntaxError) as excinfo:
        list(tokenize("x = 1 @ 2;"))
    assert "Unexpected character '@' on line 1" in str(excinfo.value)
