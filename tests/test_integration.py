import os
import pytest
from lexer import tokenize
from parser import Parser
import tac
from attributes import evaluate_attributes
from backpatch import backpatch

def eval_val(arg: str, env: dict):
    if arg is None:
        return None
    if arg == 'true':
        return True
    if arg == 'false':
        return False
    try:
        return int(arg)
    except ValueError:
        return env.get(arg, 0)

def execute_tac(instructions) -> dict:
    env = {}
    pc = 0
    max_steps = 100000
    steps = 0
    
    while pc < len(instructions):
        steps += 1
        if steps > max_steps:
            raise RuntimeError("Infinite loop or step limit exceeded in TAC interpreter!")
            
        quad = instructions[pc]
        op = quad.op
        jumped = False
        
        if op == '=':
            env[quad.result] = eval_val(quad.arg1, env)
        elif op in ('+', '-', '*', '/'):
            v1 = eval_val(quad.arg1, env)
            v2 = eval_val(quad.arg2, env)
            if op == '+':
                res = v1 + v2
            elif op == '-':
                res = v1 - v2
            elif op == '*':
                res = v1 * v2
            elif op == '/':
                res = v1 // v2  # Naive integer division
            env[quad.result] = res
        elif op == 'goto':
            assert isinstance(quad.result, int), f"Unresolved jump target in instruction {pc}: {quad}"
            pc = quad.result
            jumped = True
        elif op.startswith('if'):
            relop = op[2:]
            v1 = eval_val(quad.arg1, env)
            v2 = eval_val(quad.arg2, env)
            
            cond = False
            if relop == '<':
                cond = v1 < v2
            elif relop == '>':
                cond = v1 > v2
            elif relop == '<=':
                cond = v1 <= v2
            elif relop == '>=':
                cond = v1 >= v2
            elif relop == '==':
                cond = v1 == v2
            elif relop == '!=':
                cond = v1 != v2
                
            if cond:
                assert isinstance(quad.result, int), f"Unresolved conditional jump target in instruction {pc}: {quad}"
                pc = quad.result
                jumped = True
                
        if not jumped:
            pc += 1
            
    return env

def compile_and_run(filename: str) -> dict:
    # Reset compiler state
    tac.reset_temp()
    
    filepath = os.path.join("tests", "programs", filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        code = f.read()
        
    # Compile
    tokens = list(tokenize(code))
    parser = Parser(tokens)
    ast = parser.parse()
    evaluate_attributes(ast)
    
    # Backpatch top level
    if 'next' in ast.attrs:
        backpatch(ast.attrs['next'], tac.nextinstr())
        
    # Assert all jump targets are concrete integers
    for i, quad in enumerate(tac.instructions):
        if quad.op == 'goto' or quad.op.startswith('if'):
            assert isinstance(quad.result, int), f"Unresolved jump destination found at index {i}: {quad}"
            
    # Run in interpreter
    env = execute_tac(tac.instructions)
    return env

def test_integration_arithmetic():
    env = compile_and_run("arithmetic.txt")
    assert env.get("a") == 5
    assert env.get("b") == 10
    assert env.get("c") == 22

def test_integration_ifelse():
    env = compile_and_run("ifelse.txt")
    assert env.get("a") == 10
    assert env.get("b") == 20
    assert env.get("max") == 20

def test_integration_while():
    env = compile_and_run("while.txt")
    assert env.get("sum") == 15
    assert env.get("i") == 6

def test_integration_shortcircuit():
    env = compile_and_run("shortcircuit.txt")
    assert env.get("a") == 5
    assert env.get("b") == 10
    assert env.get("x") == 100

def test_integration_nested():
    env = compile_and_run("nested.txt")
    assert env.get("i") == 6
    assert env.get("evens") == 3
    assert env.get("odds") == 3
