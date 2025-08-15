import ast  # Import the Abstract Syntax Tree module for parsing expressions
import operator  # Import operator functions for arithmetic operations

# Supported operators mapping
operators = {
    ast.Add: operator.add,        # Addition
    ast.Sub: operator.sub,        # Subtraction
    ast.Mult: operator.mul,       # Multiplication
    ast.Div: operator.truediv,    # Division
    ast.Mod: operator.mod,        # Modulo
    ast.Pow: operator.pow,        # Exponentiation
    ast.FloorDiv: operator.floordiv  # Floor division
}

def eval_expr(expr):
    """Safely evaluate arithmetic expressions using AST"""
    try:
        node = ast.parse(expr, mode="eval").body  # Parse the expression into an AST node
        return eval_ast(node)  # Recursively evaluate the AST node
    except Exception as e:
        return f"Invalid expression: {e}"  # Return error message if parsing/evaluation fails
    
def eval_ast(node):
    """Recursively evaluate an AST node"""
    if isinstance(node, ast.Constant):  # For Python 3.8+, handle numeric constants
        if isinstance(node.value, (int, float)):  # Check if the value is a number
            return node.value  # Return the numeric value
        raise ValueError("Only numbers are allowed")  # Raise error for non-numeric constants
    elif isinstance(node, ast.BinOp):  # Handle binary operations (e.g., +, -, *, /)
        if type(node.op) not in operators:  # Check if the operator is supported
            raise ValueError(f"Unsupported operator: {type(node.op).__name__}")  # Error for unsupported operators
        left = eval_ast(node.left)  # Recursively evaluate the left operand
        right = eval_ast(node.right)  # Recursively evaluate the right operand
        return operators[type(node.op)](left, right)  # Apply the operator to operands
    elif isinstance(node, ast.UnaryOp):  # Handle unary operations (e.g., -number)
        if isinstance(node.op, ast.USub):  # Check for unary subtraction (negative numbers)
            return -eval_ast(node.operand)  # Negate the operand
        elif isinstance(node.op, ast.UAdd):  # Check for unary addition (positive numbers)
            return eval_ast(node.operand)  # Return the operand as is
        raise ValueError(f"Unsupported unary operator:  {type(node.op).__name__}")  # Error for unsupported unary operators
    raise ValueError(f"Unsupported expression: {ast.dump(node)}")  # Error for unsupported expressions

# expression = input("Enter expression: ")  # Prompt user for input expression
# print(eval_expr(expression))  # Print the result of evaluating the expression

numbers = [1, 2, 2, 3, 6, 6, 3, 7, 9, 9, 9, 3, 3]
result, count = max(((n, numbers.count(n)) for n in numbers), key=lambda x: x[1])
# count = numbers.count(result)
print(f"Result: {result} it appears {count} time/s")