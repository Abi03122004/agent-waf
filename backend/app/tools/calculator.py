import ast
import operator
from typing import Any, Dict, Union
from app.tools.base import BaseTool
from app.schemas.tool import ToolMetadata

class CalculatorTool(BaseTool):
    # Supported safe operators
    _operators: Dict[type, Any] = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.Mod: operator.mod,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos
    }

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="calculator",
            description="Safely evaluates simple mathematical expressions. Blocks dangerous function execution.",
            input_schema={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Simple mathematical expression to compute (e.g. '45 + 20')"
                    }
                },
                "required": ["expression"]
            },
            version="1.0.0",
            allowed_scope="math_evaluation"
        )

    def execute(self, expression: str, **kwargs: Any) -> str:
        try:
            # Parse with mode='eval' to only allow expressions
            node = ast.parse(expression, mode='eval')
            result = self._eval(node.body)
            # Convert calculation result to string
            return str(result)
        except Exception as e:
            raise ValueError(f"Failed to evaluate expression '{expression}' safely: {str(e)}")

    def _eval(self, node: ast.AST) -> Union[int, float]:
        if isinstance(node, ast.Num):  # Python < 3.8 compatibility
            return node.n
        elif isinstance(node, ast.Constant):  # Python >= 3.8
            if isinstance(node.value, (int, float)):
                return node.value
            raise TypeError("Only integer or float constants are allowed.")
        elif isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in self._operators:
                raise TypeError(f"Unsupported binary operator: {op_type.__name__}")
            left = self._eval(node.left)
            right = self._eval(node.right)
            
            # Division by zero protection
            if op_type == ast.Div and right == 0:
                raise ZeroDivisionError("Division by zero is not allowed.")
            
            # Resource exhaustion limits (prevent huge powers)
            if op_type == ast.Pow:
                if abs(left) > 10000 or abs(right) > 100:
                    raise ValueError("Power operation parameters exceed safety limits (max base 10000, max exponent 100).")
                
            return self._operators[op_type](left, right)
        elif isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in self._operators:
                raise TypeError(f"Unsupported unary operator: {op_type.__name__}")
            operand = self._eval(node.operand)
            return self._operators[op_type](operand)
        else:
            raise TypeError(f"Unsupported expression component: {type(node).__name__}")
