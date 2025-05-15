import json
import ast
import operator
import math
import openai
from dotenv import load_dotenv

def evaluate(expression: str) -> str:
    allowed_operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
    }
    allowed_names = {
        k: getattr(math, k)
        for k in dir(math)
        if not k.startswith("__")
    }
    allowed_names.update({
        "pi": math.pi,
        "e": math.e,
    })

    def eval_expr(node):
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Name):
            if node.id in allowed_names:
                return allowed_names[node.id]
            raise ValueError(f"Unknown identifier: {node.id}")
        elif isinstance(node, ast.BinOp):
            left = eval_expr(node.left)
            right = eval_expr(node.right)
            if type(node.op) in allowed_operators:
                return allowed_operators[type(node.op)](left, right)
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -eval_expr(node.operand)
        elif isinstance(node, ast.Call):
            func = eval_expr(node.func)
            args = [eval_expr(arg) for arg in node.args]
            return func(*args)
        raise ValueError(f"Unsupported operation: {ast.dump(node)}")

    expression = expression.replace('^', '**').replace('×', '*').replace('÷', '/')
    parsed_expr = ast.parse(expression, mode='eval')
    result = eval_expr(parsed_expr.body)
    return str(result)

load_dotenv(".env")

"""
This is a simple example to demonstrate that MCP simply enables a new way to call functions.
"""

# Define tools for the model
tools = [
    {
        "type": "function",
        "function": {
            "name": "evaluate",
            "description": "Calculates/evaluates the given expression.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "expression to evaluate and calculate"},
                },
                "required": ["expression"],
            },
        },
    }
]


response = openai.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Calculate 25 + 17"}],
    tools=tools,
)


# Handle tool calls
if response.choices[0].message.tool_calls:
    tool_call = response.choices[0].message.tool_calls[0]
    tool_name = tool_call.function.name
    tool_args = json.loads(tool_call.function.arguments)

    # Execute directly
    result = evaluate(**tool_args)

    # Send result back to model
    final_response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": "Calculate 25 + 17*2 -324"},
            response.choices[0].message,
            {"role": "tool", "tool_call_id": tool_call.id, "content": str(result)},
        ],
    )
    print(final_response.choices[0].message.content)