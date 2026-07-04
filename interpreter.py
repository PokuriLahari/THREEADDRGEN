from ast_nodes import Node

def build_symbol_table(root: Node) -> dict:
    """
    Traverses the AST and executes the program statements statically to track variables, 
    their values, types, and the line they were declared.
    """
    env = {}
    
    # 1. Initialize all variables referenced in the AST
    def collect_identifiers(node):
        if node.kind == 'IDENTIFIER':
            name = node.attrs['name']
            line = getattr(node, 'line', None)
            if name not in env:
                env[name] = {
                    'name': name,
                    'type': 'int',
                    'value': 'Uninitialized',
                    'line': line if line is not None else '-'
                }
        for child in node.children:
            collect_identifiers(child)
            
    collect_identifiers(root)
    
    # 2. Evaluate arithmetic expressions
    def eval_expr(node) -> int:
        if node.kind == 'INT_LITERAL':
            return int(node.attrs['value'])
        elif node.kind == 'IDENTIFIER':
            name = node.attrs['name']
            val = env.get(name, {}).get('value')
            if isinstance(val, (int, float)):
                return val
            return 0
        elif node.kind == 'BINOP':
            left = eval_expr(node.children[0])
            right = eval_expr(node.children[1])
            op = node.attrs['op']
            if op == '+': return left + right
            elif op == '-': return left - right
            elif op == '*': return left * right
            elif op == '/': return left // right if right != 0 else 0
        return 0

    # Evaluate boolean expressions
    def eval_bexpr(node) -> bool:
        if node.kind == 'BOOL_LITERAL':
            return node.attrs['value']
        elif node.kind == 'UNOP' and node.attrs['op'] == '!':
            return not eval_bexpr(node.children[0])
        elif node.kind == 'RELOP':
            left = eval_expr(node.children[0])
            right = eval_expr(node.children[1])
            op = node.attrs['op']
            if op == '<': return left < right
            elif op == '>': return left > right
            elif op == '<=': return left <= right
            elif op == '>=': return left >= right
            elif op == '==': return left == right
            elif op == '!=': return left != right
        elif node.kind == 'BINOP':
            op = node.attrs['op']
            if op == '&&':
                return eval_bexpr(node.children[0]) and eval_bexpr(node.children[1])
            elif op == '||':
                return eval_bexpr(node.children[0]) or eval_bexpr(node.children[1])
        return False

    # 3. Execute statement AST
    def execute(node, max_iters=1000):
        if node.kind == 'STMT_LIST':
            for child in node.children:
                execute(child)
        elif node.kind == 'ASSIGN_STMT':
            var_name = node.children[0].attrs['name']
            val = eval_expr(node.children[1])
            if var_name in env:
                env[var_name]['value'] = val
        elif node.kind == 'IF_STMT':
            if eval_bexpr(node.children[0]):
                execute(node.children[1])
        elif node.kind == 'IF_ELSE_STMT':
            if eval_bexpr(node.children[0]):
                execute(node.children[1])
            else:
                execute(node.children[2])
        elif node.kind == 'WHILE_STMT':
            iters = 0
            while eval_bexpr(node.children[0]) and iters < max_iters:
                execute(node.children[1])
                iters += 1

    execute(root)
    return env
