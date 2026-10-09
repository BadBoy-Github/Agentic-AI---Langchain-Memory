"""Calculator tool for safe mathematical evaluation."""

import ast
import operator
import math
from langchain_core.tools import tool

# Supported binary operators
_SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

# Supported mathematical functions and constants
_SAFE_FUNCTIONS = {
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "log": math.log,
    "log10": math.log10,
    "log2": math.log2,
    "exp": math.exp,
    "floor": math.floor,
    "ceil": math.ceil,
    "abs": abs,
    "round": round,
    "pow": pow,
}

_SAFE_CONSTANTS = {
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
}


def _eval_ast_node(node):
    """Recursively evaluates an AST node in a safe sandbox."""
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported constant type: {type(node.value).__name__}")

    elif isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _SAFE_OPERATORS:
            raise ValueError(f"Unsupported operator: {op_type.__name__}")
        left = _eval_ast_node(node.left)
        right = _eval_ast_node(node.right)
        op_func = _SAFE_OPERATORS[op_type]
        return op_func(left, right)

    elif isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _SAFE_OPERATORS:
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
        operand = _eval_ast_node(node.operand)
        return _SAFE_OPERATORS[op_type](operand)

    elif isinstance(node, ast.Name):
        if node.id in _SAFE_CONSTANTS:
            return _SAFE_CONSTANTS[node.id]
        raise ValueError(f"Unknown variable or constant: '{node.id}'")

    elif isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError("Unsupported dynamic function call")
        func_name = node.func.id
        if func_name not in _SAFE_FUNCTIONS:
            raise ValueError(
                f"Function '{func_name}' is not allowed. Available functions: {', '.join(_SAFE_FUNCTIONS.keys())}"
            )
        args = [_eval_ast_node(arg) for arg in node.args]
        return _SAFE_FUNCTIONS[func_name](*args)

    raise ValueError(f"Unsupported syntax expression: {type(node).__name__}")


@tool
def calculator(expression: str) -> str:
    """Safely calculates and evaluates mathematical expressions.

    Use this tool whenever you need to compute numbers, arithmetic, percentages,
    or scientific math operations.
    Examples:
      - '25 * 4 + 100 / 5'
      - '(1200 * 0.18) + 1200'
      - 'sqrt(256) + pow(2, 8)'
      - 'sin(pi / 2) + log10(100)'

    Args:
        expression: A mathematical expression string to evaluate.

    Returns:
        The numerical calculation result as a string, or an error message.
    """
    cleaned = expression.strip().replace("^", "**")
    try:
        parsed = ast.parse(cleaned, mode="eval")
        result = _eval_ast_node(parsed.body)
        # Format floating points neatly if integer equivalent
        if isinstance(result, float) and result.is_integer():
            result = int(result)
        return str(result)
    except ZeroDivisionError:
        return "Error: Division by zero."
    except Exception as err:
        return f"Error evaluating expression '{expression}': {str(err)}"
