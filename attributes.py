from ast_nodes import Node
from tac import newtemp, emit, nextinstr, Quad
from backpatch import makelist, merge, backpatch

def mark() -> int:
    """Returns the index of the next instruction to be emitted."""
    return nextinstr()

def evaluate_attributes(node: Node):
    """
    Evaluates place/code (for arithmetic), truelist/falselist (for boolean),
    or next (for statements) attributes for the given AST node using post-order traversal.
    """
    if node.kind == 'IDENTIFIER':
        place = node.attrs['name']
        code = []
        node.attrs['place'] = place
        node.attrs['code'] = code
        return place, code

    elif node.kind == 'INT_LITERAL':
        place = str(node.attrs['value'])
        code = []
        node.attrs['place'] = place
        node.attrs['code'] = code
        return place, code

    elif node.kind == 'BINOP' and node.attrs['op'] in ('+', '-', '*', '/'):
        left_place, left_code = evaluate_attributes(node.children[0])
        right_place, right_code = evaluate_attributes(node.children[1])
        
        op = node.attrs['op']
        temp = newtemp()
        instr = emit(op, left_place, right_place, temp)
        
        place = temp
        code = left_code + right_code + [instr]
        
        node.attrs['place'] = place
        node.attrs['code'] = code
        return place, code

    # Boolean expressions
    elif node.kind == 'BOOL_LITERAL':
        val = node.attrs['value']
        if val:
            truelist = makelist(nextinstr())
            emit('goto', None, None, None)
            falselist = []
        else:
            falselist = makelist(nextinstr())
            emit('goto', None, None, None)
            truelist = []
        node.attrs['truelist'] = truelist
        node.attrs['falselist'] = falselist
        return truelist, falselist

    elif node.kind == 'UNOP' and node.attrs['op'] == '!':
        truelist, falselist = evaluate_attributes(node.children[0])
        node.attrs['truelist'] = falselist
        node.attrs['falselist'] = truelist
        return falselist, truelist

    elif node.kind == 'RELOP':
        # Relational comparison: left and right are arithmetic expressions
        left_place, _ = evaluate_attributes(node.children[0])
        right_place, _ = evaluate_attributes(node.children[1])
        
        op = node.attrs['op']
        truelist = makelist(nextinstr())
        emit('if' + op, left_place, right_place, None)
        falselist = makelist(nextinstr())
        emit('goto', None, None, None)
        
        node.attrs['truelist'] = truelist
        node.attrs['falselist'] = falselist
        return truelist, falselist

    elif node.kind == 'BINOP' and node.attrs['op'] == '||':
        truelist1, falselist1 = evaluate_attributes(node.children[0])
        m_instr = nextinstr()
        truelist2, falselist2 = evaluate_attributes(node.children[1])
        
        backpatch(falselist1, m_instr)
        truelist = merge(truelist1, truelist2)
        falselist = falselist2
        
        node.attrs['truelist'] = truelist
        node.attrs['falselist'] = falselist
        return truelist, falselist

    elif node.kind == 'BINOP' and node.attrs['op'] == '&&':
        truelist1, falselist1 = evaluate_attributes(node.children[0])
        m_instr = nextinstr()
        truelist2, falselist2 = evaluate_attributes(node.children[1])
        
        backpatch(truelist1, m_instr)
        truelist = truelist2
        falselist = merge(falselist1, falselist2)
        
        node.attrs['truelist'] = truelist
        node.attrs['falselist'] = falselist
        return truelist, falselist

    # Statement Nodes
    elif node.kind == 'STMT_LIST':
        curr_next = []
        for i, child in enumerate(node.children):
            if i > 0:
                m_instr = mark()
                backpatch(curr_next, m_instr)
            curr_next = evaluate_attributes(child)
            if not isinstance(curr_next, list):
                curr_next = []
        node.attrs['next'] = curr_next
        return curr_next

    elif node.kind == 'ASSIGN_STMT':
        # children: [id_node, expr_node]
        expr_place, expr_code = evaluate_attributes(node.children[1])
        emit('=', expr_place, None, node.children[0].attrs['name'])
        node.attrs['next'] = []
        return []

    elif node.kind == 'IF_STMT':
        # children: [B, S1]
        b_truelist, b_falselist = evaluate_attributes(node.children[0])
        m_instr = mark()
        s1_next = evaluate_attributes(node.children[1])
        if not isinstance(s1_next, list):
            s1_next = []
        backpatch(b_truelist, m_instr)
        s_next = merge(b_falselist, s1_next)
        node.attrs['next'] = s_next
        return s_next

    elif node.kind == 'IF_ELSE_STMT':
        # children: [B, S1, S2]
        b_truelist, b_falselist = evaluate_attributes(node.children[0])
        m1_instr = mark()
        s1_next = evaluate_attributes(node.children[1])
        if not isinstance(s1_next, list):
            s1_next = []
        
        # insert a goto _ at the end of S1 to skip S2
        goto_idx = mark()
        emit('goto', None, None, None)
        s1_next_with_skip = merge(s1_next, makelist(goto_idx))
        
        m2_instr = mark()
        s2_next = evaluate_attributes(node.children[2])
        if not isinstance(s2_next, list):
            s2_next = []
            
        backpatch(b_truelist, m1_instr)
        backpatch(b_falselist, m2_instr)
        
        s_next = merge(s1_next_with_skip, s2_next)
        node.attrs['next'] = s_next
        return s_next

    elif node.kind == 'WHILE_STMT':
        # children: [B, S1]
        m1_instr = mark()
        b_truelist, b_falselist = evaluate_attributes(node.children[0])
        m2_instr = mark()
        s1_next = evaluate_attributes(node.children[1])
        if not isinstance(s1_next, list):
            s1_next = []
            
        backpatch(s1_next, m1_instr)
        backpatch(b_truelist, m2_instr)
        emit('goto', None, None, m1_instr)
        
        node.attrs['next'] = b_falselist
        return b_falselist

    else:
        raise ValueError(f"Unsupported AST node kind for attribute evaluation: {node.kind}")

