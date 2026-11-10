"""A bounded arithmetic interpreter. Never eval/exec, imports or shell access."""
import ast
import math
import operator
from datetime import datetime, timezone, timedelta
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

TOOL_NAMES = {'calculator', 'get_current_time', 'delegate_to_bot'}


class ToolArguments(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)


class CalculatorArguments(ToolArguments):
    expression: str = Field(min_length=1, max_length=200)


class TimeArguments(ToolArguments):
    timezone: Literal['Asia/Shanghai', 'UTC']


class DelegateArguments(ToolArguments):
    bot_name: str = Field(min_length=1, max_length=24)
    task: str = Field(min_length=1, max_length=4000)


ARGUMENT_MODELS = {'calculator': CalculatorArguments, 'get_current_time': TimeArguments, 'delegate_to_bot': DelegateArguments}


def validate_tool_args(name: str, args: dict) -> dict:
    try:
        return ARGUMENT_MODELS[name].model_validate(args).model_dump()
    except ValidationError as exc:
        # Do not echo potentially sensitive argument values in validation errors.
        fields = ', '.join('.'.join(map(str, e['loc'])) or 'arguments' for e in exc.errors())
        raise ValueError('工具参数不符合 Schema：' + fields) from None


def calculator(expression: str) -> str:
    if not isinstance(expression, str) or not expression or len(expression) > 200:
        raise ValueError('表达式长度必须为 1–200 字符')
    try:
        tree = ast.parse(expression.strip(), mode='eval')
    except (SyntaxError, RecursionError):
        raise ValueError('计算表达式语法错误') from None
    if sum(1 for _ in ast.walk(tree)) > 64:
        raise ValueError('计算表达式过于复杂')
    ops = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
           ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
           ast.Mod: operator.mod, ast.Pow: operator.pow}

    def visit(node):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            if abs(node.value) > 1e12:
                raise ValueError('数字超出允许范围')
            return node.value
        if isinstance(node, ast.UnaryOp) and type(node.op) in (ast.UAdd, ast.USub):
            return visit(node.operand) * (-1 if isinstance(node.op, ast.USub) else 1)
        if isinstance(node, ast.BinOp) and type(node.op) in ops:
            left, right = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 12:
                raise ValueError('指数绝对值不能超过 12')
            try:
                result = ops[type(node.op)](left, right)
            except (ArithmeticError, ValueError):
                raise ValueError('计算失败：除零、溢出或不支持的运算') from None
            if isinstance(result, complex) or not math.isfinite(result) or abs(result) > 1e100:
                raise ValueError('计算结果超出允许范围')
            return result
        raise ValueError('仅允许数字、括号和 + - * / // % ** 运算')

    result = visit(tree.body)
    return f'{expression.strip()} = {result:g}' if isinstance(result, float) else f'{expression.strip()} = {result}'


def get_current_time(zone: str = 'Asia/Shanghai') -> str:
    zones = {'Asia/Shanghai': timezone(timedelta(hours=8)), 'UTC': timezone.utc}
    if zone not in zones:
        raise ValueError('支持的时区：Asia/Shanghai、UTC')
    return f'{datetime.now(zones[zone]).isoformat(timespec="seconds")} ({zone})'


def tool_schemas(enabled: list[str], bots: list[dict]) -> list[dict]:
    descriptions = {
        'calculator': '安全计算器，支持数字、括号和 + - * / // % **。',
        'get_current_time': '获取服务端真实当前时间。',
        'delegate_to_bot': '将子任务交给其他房间 Bot。可用同事：' + ', '.join(b['name'] for b in bots),
    }
    return [{'type': 'function', 'function': {'name': name, 'description': descriptions[name],
             'parameters': ARGUMENT_MODELS[name].model_json_schema()}}
            for name in enabled if name in descriptions]
