from ast_nodes import Node

def to_postfix(node: Node) -> str:
    """
    Returns the space-separated postfix (Reverse Polish Notation) string 
    for the given expression AST node.
    """
    if node.kind == 'IDENTIFIER':
        return node.attrs['name']
    elif node.kind == 'INT_LITERAL':
        return str(node.attrs['value'])
    elif node.kind == 'BOOL_LITERAL':
        return 'true' if node.attrs['value'] else 'false'
    elif node.kind == 'UNOP':
        child_str = to_postfix(node.children[0])
        op = node.attrs['op']
        return f"{child_str} {op}"
    elif node.kind in ('BINOP', 'RELOP'):
        left_str = to_postfix(node.children[0])
        right_str = to_postfix(node.children[1])
        op = node.attrs['op']
        return f"{left_str} {right_str} {op}"
    elif node.kind == 'ASSIGN_STMT':
        left_str = to_postfix(node.children[0])
        right_str = to_postfix(node.children[1])
        return f"{left_str} {right_str} ="
    elif node.kind == 'STMT_LIST':
        parts = []
        for child in node.children:
            res = to_postfix(child)
            if res:
                parts.append(res)
        return "\n".join(parts)
    elif node.kind == 'IF_STMT':
        cond_str = to_postfix(node.children[0])
        then_str = to_postfix(node.children[1])
        return f"{cond_str} {then_str} if"
    elif node.kind == 'IF_ELSE_STMT':
        cond_str = to_postfix(node.children[0])
        then_str = to_postfix(node.children[1])
        else_str = to_postfix(node.children[2])
        return f"{cond_str} {then_str} {else_str} ifelse"
    elif node.kind == 'WHILE_STMT':
        cond_str = to_postfix(node.children[0])
        body_str = to_postfix(node.children[1])
        return f"{cond_str} {body_str} while"
    else:
        raise ValueError(f"Unsupported AST node kind for postfix translation: {node.kind}")


