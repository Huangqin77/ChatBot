import json
import re

import httpx

from .config import Settings


class ModelError(RuntimeError):
    pass


def validate_message(message) -> dict:
    if not isinstance(message, dict):
        raise ValueError('invalid message')
    content, calls = message.get('content'), message.get('tool_calls')
    if content is not None and not isinstance(content, str):
        raise ValueError('invalid content')
    if calls is not None and not isinstance(calls, list):
        raise ValueError('invalid tool calls')
    ids = set()
    for call in calls or []:
        if not isinstance(call, dict) or call.get('type') != 'function':
            raise ValueError('invalid tool call')
        call_id, fn = call.get('id'), call.get('function')
        if not isinstance(call_id, str) or not call_id or call_id in ids or not isinstance(fn, dict):
            raise ValueError('invalid tool call id')
        if not isinstance(fn.get('name'), str) or not fn['name'] or not isinstance(fn.get('arguments'), str):
            raise ValueError('invalid function')
        ids.add(call_id)
    if not calls and (not isinstance(content, str) or not content.strip()):
        raise ValueError('empty reply')
    return {k: message[k] for k in ('content', 'tool_calls') if k in message} | {'role': 'assistant'}


async def complete(settings: Settings, messages: list[dict], tools: list[dict]) -> dict:
    """Raw Chat Completions protocol keeps OpenAI-compatible providers usable."""
    if not settings.api_key:
        raise ModelError('Live 模式缺少 OPENAI_API_KEY；请配置后端 .env，或切换 Demo 模式。')
    payload = {'model': settings.model, 'messages': messages, 'stream': False}
    if tools:
        payload.update(tools=tools, tool_choice='auto')
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(45, connect=10)) as client:
            response = await client.post(settings.base_url.rstrip('/') + '/chat/completions',
                                         headers={'Authorization': f'Bearer {settings.api_key}'}, json=payload)
        if response.is_error:
            # Never echo provider bodies: they can include credentials or upstream HTML.
            raise ModelError(f'模型 API 返回 HTTP {response.status_code}，请检查后端 Key、Base URL、Model 和额度。')
        choice = response.json()['choices'][0]
        if choice.get('finish_reason') in {'length', 'content_filter'}:
            raise ModelError('模型回复被截断或拦截，本次任务未完成，请调整请求后重试。')
        return validate_message(choice['message'])
    except httpx.TimeoutException:
        raise ModelError('模型请求超时，请稍后重试。') from None
    except httpx.RequestError:
        raise ModelError('无法连接模型服务，请检查 Base URL 和网络。') from None
    except (ValueError, KeyError, IndexError, TypeError, AttributeError):
        raise ModelError('模型返回了无效的 Chat Completions 响应。') from None


def demo_plan(bot: dict, request: str, peers: list[dict], depth: int) -> list[tuple[str, dict]]:
    """Intentionally deterministic demo; no generated answer is labeled as live."""
    enabled = bot['tools']
    if depth == 0 and re.search(r'委派|协作|合作|delegate', request, re.I) and 'delegate_to_bot' in enabled:
        others = [b for b in peers if b['id'] != bot['id']]
        target = next((b for b in others if b['name'] in request), others[0] if others else None)
        if target:
            return [('delegate_to_bot', {'bot_name': target['name'], 'task': request})]
    calls = []
    # Extract arithmetic, never interpret general text as Python.
    expressions = [s.strip().rstrip('. ') for s in re.findall(r'[\d().+*/%\-][\d().+*/%\-\s]*', request)]
    expressions = [s for s in expressions if re.search(r'\d', s) and re.search(r'[+*/%\-]', s)]
    if expressions and 'calculator' in enabled:
        calls.append(('calculator', {'expression': max(expressions, key=len)}))
    if re.search(r'时间|几点|time|日期', request, re.I) and 'get_current_time' in enabled:
        calls.append(('get_current_time', {'timezone': 'Asia/Shanghai'}))
    return calls


def demo_answer(bot: dict, request: str, outputs: list[str]) -> str:
    if outputs:
        return '[Demo / Mock · 规则演示，工具真实执行]\n' + '\n\n'.join(outputs) + '\n\n以上是本次任务的执行汇总。'
    return (f'[Demo / Mock · 非真实模型调用]\n我是{bot["name"]}（{bot["role"]}）。已收到：{request[:500]}\n\n'
            '演示模式支持算式、当前时间，以及带“委派 / 协作”的任务。'
            '自由对话和按 System Prompt 推理需要在后端配置模型 API。')
