class Node:
    """A uniform AST Node class containing kind, children, and an attrs dict."""
    def __init__(self, kind: str, children: list = None, attrs: dict = None):
        self.kind = kind
        self.children = children if children is not None else []
        self.attrs = attrs if attrs is not None else {}

    def __repr__(self) -> str:
        attrs_str = f", attrs={self.attrs}" if self.attrs else ""
        children_str = f", children={self.children}" if self.children else ""
        return f"Node(kind={self.kind!r}{attrs_str}{children_str})"

    def to_str(self, indent: int = 0) -> str:
        """Returns the AST formatted as an indented tree string."""
        space = "  " * indent
        attrs_part = f" {self.attrs}" if self.attrs else ""
        res = f"{space}{self.kind}{attrs_part}\n"
        for child in self.children:
            res += child.to_str(indent + 1)
        return res

    def __str__(self) -> str:
        return self.to_str().rstrip('\n')
