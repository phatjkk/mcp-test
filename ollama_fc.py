import ast
import operator
import math
from dotenv import load_dotenv
import asyncio
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

import ollama
async def main():
    client = ollama.AsyncClient()
    available_functions = {
    'evaluate': evaluate,
    }
    model_name = 'qwen3:1.7b'
    messages = [{'role': 'user', 'content': 'What is three plus one?'}]
    response = ollama.chat(
                            model_name,
                            messages=messages,
                            tools=[evaluate], # Actual function reference
                            )
    print(response)
    if response.message.tool_calls:
        # There may be multiple tool calls in the response
        for tool in response.message.tool_calls:
            # Ensure the function is available, and then call it
            if function_to_call := available_functions.get(tool.function.name):
                print('Calling function:', tool.function.name)
                print('Arguments:', tool.function.arguments)
                output = function_to_call(**tool.function.arguments)
                print('Function output:', output)
            else:
                print('Function', tool.function.name, 'not found')

    # Only needed to chat with the model using the tool call results
    if response.message.tool_calls:
        # Add the function response to messages for the model to use
        messages.append(response.message)
        messages.append({'role': 'tool', 'content': str(output), 'name': tool.function.name})

        # Get final response from model with function outputs
        final_response = await client.chat(model_name, messages=messages)
        print('Final response:', final_response.message.content)

    else:
        print('No tool calls returned from model')


if __name__ == '__main__':
  try:
    asyncio.run(main())
  except KeyboardInterrupt:
    print('\nGoodbye!')
