import sys
from lexer import tokenize
from parser import Parser
import tac
from attributes import evaluate_attributes
from postfix import to_postfix

def main():
    visualize_mode = False
    code = None

    if len(sys.argv) > 1:
        if sys.argv[1] == '--visualize':
            visualize_mode = True
            if len(sys.argv) > 2:
                arg = sys.argv[2]
                try:
                    with open(arg, 'r', encoding='utf-8') as f:
                        code = f.read()
                except OSError:
                    code = arg
            else:
                # Default program
                code = (
                    "i = 0;\n"
                    "while (i < n) {\n"
                    "    if (i < 5) {\n"
                    "        x = x + 1;\n"
                    "    } else {\n"
                    "        x = x + 2;\n"
                    "    }\n"
                    "    i = i + 1;\n"
                    "}"
                )
        else:
            arg = sys.argv[1]
            try:
                with open(arg, 'r', encoding='utf-8') as f:
                    code = f.read()
            except OSError:
                code = arg
    else:
        # Default now tests a while statement
        code = (
            "i = 0;\n"
            "while (i < n) {\n"
            "    if (i < 5) {\n"
            "        x = x + 1;\n"
            "    } else {\n"
            "        x = x + 2;\n"
            "    }\n"
            "    i = i + 1;\n"
            "}"
        )
        print(f"No input provided. Parsing default input:\n{code}\n")

    try:
        # Reset the temporary variable counter and instructions list before each evaluation
        tac.reset_temp()
        
        # Tokenize
        tokens = list(tokenize(code))
        
        # Parse
        parser = Parser(tokens)
        ast = parser.parse()
        
        # Evaluate attributes (TAC generation in global instruction list)
        evaluate_attributes(ast)
        
        # Backpatch any remaining open next lists to the final instruction index (end of program)
        if 'next' in ast.attrs:
            from backpatch import backpatch
            backpatch(ast.attrs['next'], tac.nextinstr())
            
        # Collect TAC lines
        tac_lines = []
        if tac.instructions:
            for i, quad in enumerate(tac.instructions):
                tac_lines.append(f"{i}: {quad}")
        else:
            leaf_val = ast.attrs.get('name') or ast.attrs.get('value')
            tac_lines.append(f"# No operations emitted (leaf value: {leaf_val})")
            
        # Collect Postfix lines
        postfix_str = ""
        try:
            postfix_str = to_postfix(ast)
        except ValueError:
            pass
        postfix_lines = postfix_str.split("\n") if postfix_str else []

        if visualize_mode:
            # Generate visualization and save to output.svg
            from visualizer import visualize_ast
            visualize_ast(ast, "output")
            
            # Print side-by-side
            left_title = "Three Address Code (TAC):"
            right_title = "Postfix Notation:"
            gutter = "  |  "
            
            max_tac_len = max(len(line) for line in tac_lines) if tac_lines else 0
            max_tac_len = max(max_tac_len, len(left_title))
            
            print(f"{left_title.ljust(max_tac_len)}{gutter}{right_title}")
            print(f"{'-' * max_tac_len}{gutter}{'-' * len(right_title)}")
            
            max_lines = max(len(tac_lines), len(postfix_lines))
            for i in range(max_lines):
                tac_col = tac_lines[i] if i < len(tac_lines) else ""
                postfix_col = postfix_lines[i] if i < len(postfix_lines) else ""
                print(f"{tac_col.ljust(max_tac_len)}{gutter}{postfix_col}")
            print()
        else:
            print("Abstract Syntax Tree:")
            print(ast)
            print()
            
            print("Three Address Code (TAC):")
            for line in tac_lines:
                print(line)
            print()
            
            # Print truelist/falselist for boolean expressions, or nextlist for statements
            if 'truelist' in ast.attrs or 'falselist' in ast.attrs:
                print(f"B.truelist: {ast.attrs.get('truelist', [])}")
                print(f"B.falselist: {ast.attrs.get('falselist', [])}")
                print()
            elif 'next' in ast.attrs:
                print(f"S.next: {ast.attrs.get('next', [])}")
                print()
                
            if postfix_str:
                print("Postfix Notation:")
                print(postfix_str)
                print()
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

