import re
import sys
from typing import Generator

class Token:
    """Represents a token in the C-like language."""
    def __init__(self, type: str, value: str, line: int):
        self.type = type
        self.value = value
        self.line = line

    def __repr__(self) -> str:
        return f"Token({self.type}, {self.value!r}, {self.line})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Token):
            return NotImplemented
        return self.type == other.type and self.value == other.value and self.line == other.line


def tokenize(code: str) -> Generator[Token, None, None]:
    """Tokenize the input C-like code into a sequence of Token objects."""
    keywords = {'if', 'else', 'while', 'true', 'false'}
    
    # Mapping for operator/punctuation types
    op_punct_map = {
        '+': 'PLUS',
        '-': 'MINUS',
        '*': 'TIMES',
        '/': 'DIVIDE',
        '=': 'ASSIGN',
        '==': 'EQ',
        '!=': 'NE',
        '<': 'LT',
        '>': 'GT',
        '<=': 'LE',
        '>=': 'GE',
        '&&': 'AND',
        '||': 'OR',
        '!': 'NOT',
        '(': 'LPAREN',
        ')': 'RPAREN',
        '{': 'LBRACE',
        '}': 'RBRACE',
        ';': 'SEMICOLON',
    }

    # Define regex pattern pairs. Order is important (double characters before single characters).
    token_specification = [
        ('COMMENT_MULTI',  r'/\*[\s\S]*?\*/'),
        ('COMMENT_SINGLE', r'//.*'),
        ('EQ',             r'=='),
        ('NE',             r'!='),
        ('LE',             r'<='),
        ('GE',             r'>='),
        ('AND',            r'&&'),
        ('OR',             r'\|\|'),
        ('LT',             r'<'),
        ('GT',             r'>'),
        ('ASSIGN',         r'='),
        ('PLUS',           r'\+'),
        ('MINUS',          r'-'),
        ('TIMES',          r'\*'),
        ('DIVIDE',         r'/'),
        ('NOT',            r'!'),
        ('LPAREN',         r'\('),
        ('RPAREN',         r'\)'),
        ('LBRACE',         r'\{'),
        ('RBRACE',         r'\}'),
        ('SEMICOLON',      r';'),
        ('INT_LITERAL',    r'\d+'),
        ('IDENTIFIER',     r'[a-zA-Z_][a-zA-Z0-9_]*'),
        ('NEWLINE',        r'\n'),
        ('SKIP',           r'[ \t\r]+'),
        ('MISMATCH',       r'.'),
    ]

    # Combine patterns into a single regular expression with named groups
    master_re = re.compile('|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_specification))
    
    line = 1
    for match in master_re.finditer(code):
        token_type = match.lastgroup
        token_value = match.group(token_type)
        
        if token_type == 'NEWLINE':
            line += 1
            continue
        elif token_type == 'SKIP':
            continue
        elif token_type == 'COMMENT_SINGLE':
            continue
        elif token_type == 'COMMENT_MULTI':
            line += token_value.count('\n')
            continue
        elif token_type == 'MISMATCH':
            raise SyntaxError(f"Unexpected character {token_value!r} on line {line}")
            
        if token_type == 'IDENTIFIER':
            if token_value in keywords:
                # Use uppercase keyword value as token type, e.g. 'IF', 'ELSE', 'WHILE', 'TRUE', 'FALSE'
                token_type = token_value.upper()
        elif token_type in op_punct_map:
            # Map operator/punctuation symbols to descriptive type names
            token_type = op_punct_map[token_value]
            
        yield Token(token_type, token_value, line)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python lexer.py <filename>", file=sys.stderr)
        sys.exit(1)
        
    filename = sys.argv[1]
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            file_content = f.read()
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.", file=sys.stderr)
        sys.exit(1)
        
    try:
        for tok in tokenize(file_content):
            print(tok)
    except SyntaxError as e:
        print(f"Lexical error: {e}", file=sys.stderr)
        sys.exit(1)
