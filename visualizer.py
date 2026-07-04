import html
import graphviz
from ast_nodes import Node

def make_label(node: Node) -> str:
    kind = node.kind
    attrs_rows = []

    # Category checks based on node kind and presence of attributes
    is_stmt = 'next' in node.attrs or kind in ('STMT_LIST', 'ASSIGN_STMT', 'IF_STMT', 'IF_ELSE_STMT', 'WHILE_STMT')
    is_bool = 'truelist' in node.attrs or 'falselist' in node.attrs or kind in ('BOOL_LITERAL', 'RELOP')
    is_expr = 'place' in node.attrs or 'code' in node.attrs or kind in ('IDENTIFIER', 'INT_LITERAL')

    if is_stmt:
        header_color = '#7C3AED'  # Violet accent for statements
        nextlist = node.attrs.get('next', [])
        attrs_rows.append(f"next: {nextlist}")
    elif is_bool:
        header_color = '#0D9488'  # Teal accent for booleans
        truelist = node.attrs.get('truelist', [])
        falselist = node.attrs.get('falselist', [])
        attrs_rows.append(f"truelist: {truelist}")
        attrs_rows.append(f"falselist: {falselist}")
    elif is_expr:
        header_color = '#2563EB'  # Blue accent for expressions
        place = node.attrs.get('place', '')
        code = node.attrs.get('code', [])
        code_str = ", ".join(str(q) for q in code) if code else "[]"
        attrs_rows.append(f"place: {place}")
        attrs_rows.append(f"code: {code_str}")
    else:
        header_color = '#334155'  # Slate gray for operators/other nodes

    # Include other specific attributes (like name, value, op)
    specific_parts = []
    for k, v in node.attrs.items():
        if k not in ('place', 'code', 'truelist', 'falselist', 'next', 'line'):
            specific_parts.append(f"{k}: {v}")
    if specific_parts:
        attrs_rows.append(", ".join(specific_parts))

    # Build HTML table for label
    escaped_kind = html.escape(kind)
    rows = [f"<tr><td bgcolor='{header_color}'><font color='#ffffff'><b>{escaped_kind}</b></font></td></tr>"]
    for attr in attrs_rows:
        escaped_attr = html.escape(attr)
        rows.append(f"<tr><td><font color='#e2e8f0'>{escaped_attr}</font></td></tr>")

    label = f"<<table border='1' color='#475569' cellborder='1' cellspacing='0' cellpadding='4'>{''.join(rows)}</table>>"
    return label

def visualize_ast(root: Node, filename: str = "output") -> str:
    """
    Walks the AST, creates a Graphviz visualization, writes filename.svg, 
    and returns the SVG source code as a string.
    """
    dot = graphviz.Digraph(comment='Annotated AST', format='svg')
    dot.attr('node', shape='none', fontname='Outfit')
    dot.attr('edge', fontname='Outfit', color='#475569')
    dot.attr(bgcolor='transparent')

    node_counter = 0

    def walk(node):
        nonlocal node_counter
        node_id = f"node{node_counter}"
        node_counter += 1

        label = make_label(node)
        dot.node(node_id, label)

        for child in node.children:
            child_id = walk(child)
            dot.edge(node_id, child_id)

        return node_id

    walk(root)

    # Render/save to filename.svg
    dot.render(filename, cleanup=True)

    # Pipe format='svg' to get the string representation
    svg_bytes = dot.pipe(format='svg')
    return svg_bytes.decode('utf-8')
