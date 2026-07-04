from lexer import Token
from ast_nodes import Node

class Parser:
    """A recursive-descent parser for C-like language arithmetic and boolean expressions."""
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.current = 0

    def is_statement_input(self) -> bool:
        """Determines if the token stream represents statements/program rather than an expression."""
        if self.is_at_end():
            return False
        first = self.peek()
        if first.type in ('IF', 'WHILE', 'LBRACE'):
            return True
        if first.type == 'IDENTIFIER':
            # Check if there is an assignment op next
            if self.current + 1 < len(self.tokens):
                return self.tokens[self.current + 1].type == 'ASSIGN'
        return False

    def parse(self) -> Node:
        """Parses the expression or statements and returns the AST root Node."""
        if not self.tokens:
            raise SyntaxError("Empty token stream")
        
        if self.is_statement_input():
            node = self.parse_stmt_list()
        else:
            # Auto-detect if this is a boolean or arithmetic expression
            is_bool = False
            for t in self.tokens:
                if t.type in ('OR', 'AND', 'NOT', 'TRUE', 'FALSE', 'LT', 'GT', 'LE', 'GE', 'EQ', 'NE'):
                    is_bool = True
                    break

            if is_bool:
                node = self.parse_bexpr()
            else:
                node = self.parse_expr()

        if not self.is_at_end():
            curr = self.peek()
            raise SyntaxError(f"Unexpected token {curr.value!r} after expression/statements on line {curr.line}")
        return node

    def parse_stmt_list(self) -> Node:
        """StmtList -> Stmt StmtList | ε"""
        stmts = []
        while not self.is_at_end() and self.peek().type != 'RBRACE':
            stmts.append(self.parse_stmt())
        return Node('STMT_LIST', children=stmts)

    def parse_stmt(self) -> Node:
        """
        Stmt -> id = Expr ;
              | if ( BExpr ) Stmt (else Stmt)?
              | while ( BExpr ) Stmt
              | { StmtList }
        """
        if self.match('IF'):
            self.consume('LPAREN', "Expect '(' after 'if'.")
            bexpr = self.parse_bexpr()
            self.consume('RPAREN', "Expect ')' after condition.")
            then_branch = self.parse_stmt()
            if self.match('ELSE'):
                else_branch = self.parse_stmt()
                return Node('IF_ELSE_STMT', children=[bexpr, then_branch, else_branch])
            return Node('IF_STMT', children=[bexpr, then_branch])
        
        elif self.match('WHILE'):
            self.consume('LPAREN', "Expect '(' after 'while'.")
            bexpr = self.parse_bexpr()
            self.consume('RPAREN', "Expect ')' after condition.")
            body = self.parse_stmt()
            return Node('WHILE_STMT', children=[bexpr, body])
            
        elif self.match('LBRACE'):
            stmt_list = self.parse_stmt_list()
            self.consume('RBRACE', "Expect '}' after statement list.")
            return stmt_list
            
        elif self.match('IDENTIFIER'):
            id_token = self.previous()
            self.consume('ASSIGN', "Expect '=' after identifier.")
            expr = self.parse_expr()
            self.consume('SEMICOLON', "Expect ';' after assignment.")
            id_node = Node('IDENTIFIER', attrs={'name': id_token.value})
            id_node.line = id_token.line
            return Node('ASSIGN_STMT', children=[id_node, expr])
            
        else:
            curr = self.peek()
            raise SyntaxError(f"Expect statement, found {curr.value!r} on line {curr.line}")

    def parse_bexpr(self) -> Node:
        """BExpr -> BTerm BExprRest"""
        node = self.parse_bterm()
        while self.match('OR'):
            op_token = self.previous()
            right = self.parse_bterm()
            node = Node('BINOP', children=[node, right], attrs={'op': '||'})
        return node

    def parse_bterm(self) -> Node:
        """BTerm -> BFactor BTermRest"""
        node = self.parse_bfactor()
        while self.match('AND'):
            op_token = self.previous()
            right = self.parse_bfactor()
            node = Node('BINOP', children=[node, right], attrs={'op': '&&'})
        return node

    def parse_bfactor(self) -> Node:
        """BFactor -> ! BFactor | ( BExpr ) | true | false | Expr relop Expr"""
        if self.match('NOT'):
            child = self.parse_bfactor()
            return Node('UNOP', children=[child], attrs={'op': '!'})
        elif self.match('TRUE'):
            return Node('BOOL_LITERAL', attrs={'value': True})
        elif self.match('FALSE'):
            return Node('BOOL_LITERAL', attrs={'value': False})
        elif self.peek().type == 'LPAREN':
            if self.is_parenthesized_bexpr():
                self.consume('LPAREN', "Expect '(' before boolean expression.")
                node = self.parse_bexpr()
                self.consume('RPAREN', "Expect ')' after boolean expression.")
                return node
            else:
                left = self.parse_expr()
                op = self.consume_relop()
                right = self.parse_expr()
                return Node('RELOP', children=[left, right], attrs={'op': op})
        else:
            left = self.parse_expr()
            op = self.consume_relop()
            right = self.parse_expr()
            return Node('RELOP', children=[left, right], attrs={'op': op})

    def consume_relop(self) -> str:
        """Consumes and returns a relational operator."""
        relops = ('LT', 'GT', 'LE', 'GE', 'EQ', 'NE')
        for op_type in relops:
            if self.match(op_type):
                return self.previous().value
        curr = self.peek()
        raise SyntaxError(f"Expect relational operator. Found {curr.value!r} on line {curr.line}")

    def is_parenthesized_bexpr(self) -> bool:
        """Helper to scan lookahead tokens to check if parenthesized block is a BExpr."""
        depth = 0
        has_boolean_token = False
        for i in range(self.current, len(self.tokens)):
            t = self.tokens[i]
            if t.type == 'LPAREN':
                depth += 1
            elif t.type == 'RPAREN':
                depth -= 1
                if depth == 0:
                    break
            elif depth >= 1:
                if t.type in ('OR', 'AND', 'NOT', 'TRUE', 'FALSE', 'LT', 'GT', 'LE', 'GE', 'EQ', 'NE'):
                    has_boolean_token = True
        return has_boolean_token

    def parse_expr(self) -> Node:
        """Expr -> Term ExprRest"""
        node = self.parse_term()
        while self.match('PLUS', 'MINUS'):
            op_token = self.previous()
            right = self.parse_term()
            node = Node('BINOP', children=[node, right], attrs={'op': op_token.value})
        return node

    def parse_term(self) -> Node:
        """Term -> Factor TermRest"""
        node = self.parse_factor()
        while self.match('TIMES', 'DIVIDE'):
            op_token = self.previous()
            right = self.parse_factor()
            node = Node('BINOP', children=[node, right], attrs={'op': op_token.value})
        return node

    def parse_factor(self) -> Node:
        """Factor -> ( Expr ) | id | num"""
        if self.match('INT_LITERAL'):
            token = self.previous()
            return Node('INT_LITERAL', attrs={'value': int(token.value)})
        elif self.match('IDENTIFIER'):
            token = self.previous()
            node = Node('IDENTIFIER', attrs={'name': token.value})
            node.line = token.line
            return node
        elif self.match('LPAREN'):
            node = self.parse_expr()
            self.consume('RPAREN', "Expect ')' after expression.")
            return node
        else:
            curr = self.peek()
            raise SyntaxError(f"Expect expression at token {curr.value!r} on line {curr.line}")

    # Helper methods for stream traversal
    def is_at_end(self) -> bool:
        return self.current >= len(self.tokens)

    def peek(self) -> Token:
        if self.is_at_end():
            # Return an EOF token for clean error formatting
            last_line = self.tokens[-1].line if self.tokens else 1
            return Token('EOF', '', last_line)
        return self.tokens[self.current]

    def previous(self) -> Token:
        return self.tokens[self.current - 1]

    def advance(self) -> Token:
        if not self.is_at_end():
            self.current += 1
        return self.previous()

    def check(self, *types: str) -> bool:
        if self.is_at_end():
            return False
        return self.peek().type in types

    def match(self, *types: str) -> bool:
        if self.check(*types):
            self.advance()
            return True
        return False

    def consume(self, type_: str, message: str) -> Token:
        if self.check(type_):
            return self.advance()
        curr = self.peek()
        raise SyntaxError(f"{message} Found {curr.value!r} on line {curr.line}")

