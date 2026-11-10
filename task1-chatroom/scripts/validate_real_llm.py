"""Opt-in real-provider acceptance. No fixtures, fallback or automatic retry.

Missing credentials => exit 2 / NOT RUN, with zero provider requests.
Reports contain only this isolated test's data; never headers or session tokens.
"""
import argparse
import asyncio
import hashlib
import json
import logging
import socket
import sqlite3
import sys
import threading
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))

import httpx
import uvicorn
from websockets.asyncio.client import connect

from app import llm
from app.config import Settings
from app.main import create_app

CHECKS = ('connectivity', 'calculator', 'tool_result_return', 'delegate_to_bot',
          'child_execution', 'parent_summary', 'websocket', 'sqlite')
CALCULATOR_PROMPT = '@数据助手 请使用计算工具计算 128 × 36，并告诉我计算结果。'
DELEGATE_PROMPT = '@规划助手 请把“计算 128 × 36”这个任务委派给数据助手，等待数据助手返回计算结果后，再由你总结并回复我。'


def require(condition, explanation):
    if not condition:
        raise ValueError(explanation)


def clean(value, secret):
    if isinstance(value, dict):
        return {k: clean(v, secret) for k, v in value.items()
                if k.lower() not in {'authorization', 'api_key', 'token', 'headers'}}
    if isinstance(value, list):
        return [clean(v, secret) for v in value]
    if isinstance(value, str) and secret:
        return value.replace(secret, '[REDACTED]')
    return value


class RequestAudit:
    """Observe and forward the original complete(); never synthesize a response."""
    def __init__(self, original, maximum):
        self.original, self.maximum = original, maximum
        self.phase, self.entries = 'connectivity', []

    async def complete(self, settings, messages, tools):
        if len(self.entries) >= self.maximum:
            raise llm.ModelError('真实验收请求预算已耗尽；停止执行，不自动重试。')
        system = messages[0].get('content', '') if messages else ''
        bot = next((name for name in ('规划助手', '数据助手') if system.startswith('你是' + name)), 'connectivity')
        submitted = [{'provider_call_id': m['tool_call_id'], 'output': m['content'][:2000]}
                     for m in messages if m['role'] == 'tool']
        ids = {c['id'] for m in messages for c in (m.get('tool_calls') or [])}
        require(all(m['provider_call_id'] in ids for m in submitted), '工具回填未关联原 assistant tool_call_id')
        entry = {'sequence': len(self.entries) + 1, 'time': datetime.now(timezone.utc).isoformat(),
                 'phase': self.phase, 'bot': bot, 'system_prompt_sha256': hashlib.sha256(system.encode()).hexdigest(),
                 'submitted_tool_results': submitted, 'status': 'request_started'}
        self.entries.append(entry)
        try:
            reply = await self.original(settings, messages, tools)
            entry.update(status='response_accepted', native_tool_calls=[
                {'provider_call_id': c['id'], 'name': c['function']['name'],
                 'arguments': c['function']['arguments']} for c in (reply.get('tool_calls') or [])],
                final_text_length=len(reply.get('content') or ''))
            return reply
        except BaseException as exc:
            entry['status'] = 'failed'
            entry['error'] = str(exc)[:800] if isinstance(exc, llm.ModelError) else type(exc).__name__
            raise


def check_scenario(state, reply, planner, analyst, audit, delegated):
    task = next(t for t in state['tasks'] if t['id'] == reply['task_id'])
    chain = [t for t in state['tasks'] if t['root_id'] == task['id']]
    calls = [c for c in state['tool_calls'] if c['root_id'] == task['id']]
    require(task['status'] == 'completed' and reply['kind'] == 'bot', '主任务未完成或返回了系统错误')
    require(all(t['mode'] == 'live' and t['status'] == 'completed' for t in chain), '任务链不是全部 Live / completed')
    require(len(calls) <= 6 and max(t['depth'] for t in chain) <= 2, '工具预算或深度超限')
    require('4608' in reply['content'], '最终答复未包含验收结果 4608')
    phase = 'delegation' if delegated else 'calculator'
    entries = [e for e in audit.entries if e['phase'] == phase]
    native = [(e['bot'], c) for e in entries for c in e.get('native_tool_calls', [])]
    require(calls and all(c.get('provider_call_id') and c['status'] == 'completed' for c in calls),
            '没有原生工具调用证据，或持久化调用 ID 未与模型响应对应；直接心算不能通过')
    for call in calls:
        owner = next(t['bot_name'] for t in chain if t['id'] == call['task_id'])
        require(any(bot == owner and origin['provider_call_id'] == call['provider_call_id'] and
                    origin['name'] == call['name'] and json.loads(origin['arguments']) == call['input']
                    for bot, origin in native), '模型原生调用 ID / Bot / 持久化参数不符')
        require(any(r['provider_call_id'] == call['provider_call_id'] for e in entries if e['bot'] == owner for r in e['submitted_tool_results']),
                '工具结果未通过原始 tool_call_id 返回模型')
    calculators = [c for c in calls if c['name'] == 'calculator']
    require(calculators and any(c['output'].partition('=')[2].strip() == '4608' for c in calculators), '未实际执行 calculator 得到 4608')
    if delegated:
        delegation = next((c for c in calls if c['name'] == 'delegate_to_bot' and c['task_id'] == task['id']), None)
        require(delegation is not None, '主 Bot 未使用原生 delegate_to_bot')
        child = next((t for t in chain if t['id'] == delegation['child_task_id']), None)
        require(child and child['parent_id'] == task['id'] and child['bot_id'] == analyst['id'], '子任务未交给独立数据助手')
        require(task['bot_id'] == planner['id'] != child['bot_id'], '主子 Bot 身份错误')
        require(any(c['task_id'] == child['id'] for c in calculators), 'calculator 未由子 Bot 执行')
        require(any(e['bot'] == '规划助手' and e['submitted_tool_results'] and e.get('final_text_length', 0) for e in entries),
                '主 Bot 没有收到委派结果后继续请求模型并生成总结')
        require(any(e['bot'] == '数据助手' for e in entries), '没有子 Bot 独立 System Prompt 的请求证据')
    else:
        require(task['bot_id'] == analyst['id'] and len(chain) == 1, '直接计算任务身份不符')
    return {'root_task_id': task['id'], 'tasks': chain, 'tool_calls': calls,
            'final_message': {k: reply[k] for k in ('id', 'sender_id', 'sender_name', 'content', 'task_id', 'mode')}}


async def receive_until(ws, predicate):
    async with asyncio.timeout(130):
        for _ in range(200):
            event = json.loads(await ws.recv())
            if event['type'] == 'error':
                raise ValueError(event['message'])
            if predicate(event):
                return event
    raise ValueError('WebSocket 未返回预期事件')


async def business_checks(settings, folder, audit, report):
    db_path = folder / 'validation.db'
    app = create_app(replace(settings, mode='live', database_url='sqlite:///' + db_path.as_posix()))
    listener = socket.socket()
    listener.bind(('127.0.0.1', 0))
    listener.listen(128)
    listener.setblocking(False)
    port = listener.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, log_level='warning', access_log=False, timeout_graceful_shutdown=2))
    thread = threading.Thread(target=server.run, kwargs={'sockets': [listener]}, daemon=True)
    thread.start()
    try:
        for _ in range(200):
            if server.started:
                break
            require(thread.is_alive(), '临时验收后端启动失败')
            await asyncio.sleep(.05)
        require(server.started, '临时验收后端启动超时')
        async with httpx.AsyncClient(base_url=f'http://127.0.0.1:{port}', timeout=10) as client:
            async def api(method, path, data=None):
                response = await client.request(method, '/api' + path, json=data)
                require(response.is_success, f'本地 API {path} 返回 {response.status_code}')
                return response.json()

            user = await api('POST', '/users', {'nickname': '真实模型验收'})
            client.headers['Authorization'] = 'Bearer ' + user['token']
            room = await api('POST', '/rooms', {'name': '真实 LLM 最小验收', 'description': '独立验收数据库'})
            analyst = await api('POST', '/bots', {'name': '数据助手', 'role': '独立计算子任务', 'tools': ['calculator'],
                'system_prompt': '你是数据助手。所有数学运算必须使用 calculator，不能心算。将乘法符号转换为 *。收到工具结果后用中文简洁回答。'})
            planner = await api('POST', '/bots', {'name': '规划助手', 'role': '委派并汇总', 'tools': ['delegate_to_bot'],
                'system_prompt': '你是规划助手。收到计算任务时必须用 delegate_to_bot 委派给数据助手，不得自行计算或假扮数据助手。等待委派结果后基于返回内容用中文总结。'})
            await api('PUT', f'/rooms/{room["id"]}/bots', {'bot_ids': [analyst['id'], planner['id']]})
            report['bot_ids'] = {'planner': planner['id'], 'analyst': analyst['id']}
            ws_url = f'ws://127.0.0.1:{port}/ws/rooms/{room["id"]}?token={user["token"]}'
            async with connect(ws_url) as ws:
                await receive_until(ws, lambda e: e['type'] == 'snapshot')
                for delegated, prompt in ((False, CALCULATOR_PROMPT), (True, DELEGATE_PROMPT)):
                    audit.phase = 'delegation' if delegated else 'calculator'
                    report['active_check'] = 'delegate_to_bot' if delegated else 'calculator'
                    await ws.send(json.dumps({'type': 'message', 'content': prompt, 'client_id': uuid4().hex}))
                    terminal = await receive_until(ws, lambda e: e['type'] == 'message' and e['message']['task_id'] is not None)
                    state = await api('GET', f'/rooms/{room["id"]}/state')
                    # Preserve the genuine trace even when an assertion fails (e.g. direct mental calculation).
                    report.setdefault('observed_states', []).append({'phase': audit.phase, 'tasks': state['tasks'], 'tool_calls': state['tool_calls']})
                    evidence = check_scenario(state, terminal['message'], planner, analyst, audit, delegated)
                    report.setdefault('scenarios', []).append(evidence)
                    if delegated:
                        for key in ('delegate_to_bot', 'child_execution', 'parent_summary'):
                            report['checks'][key] = 'PASS'
                    else:
                        report['checks']['calculator'] = report['checks']['tool_result_return'] = 'PASS'
                report['checks']['websocket'] = 'PASS'
            report['active_check'] = 'sqlite'
            async with connect(ws_url) as ws:
                restored = await receive_until(ws, lambda e: e['type'] == 'snapshot')
            require(restored['messages'] == state['messages'] and restored['tasks'] == state['tasks'] and
                    restored['tool_calls'] == state['tool_calls'], '重连快照与持久化记录不一致')
            with sqlite3.connect(db_path) as database:
                for table, rows in (('tasks', state['tasks']), ('tool_calls', state['tool_calls'])):
                    saved_ids = {r[0] for r in database.execute(f'SELECT id FROM {table}')}
                    require({r['id'] for r in rows} <= saved_ids, 'SQLite 独立连接未读取到已提交记录')
            report['checks']['sqlite'] = 'PASS'
            report['database'] = str(db_path)
    finally:
        server.should_exit = True
        await asyncio.to_thread(thread.join, 10)
        listener.close()


def initial_report(settings, maximum):
    return {'time': datetime.now(timezone.utc).isoformat(), 'model': settings.model, 'base_url': settings.base_url,
              'configured_mode': settings.mode, 'execution_mode': 'not_run', 'api_key_configured': bool(settings.api_key),
              'request_budget': maximum, 'external_requests_attempted': 0, 'checks': {name: 'NOT RUN' for name in CHECKS},
              'real_browser_ui': 'NOT RUN', 'trace': [], 'conclusion': 'C'}


async def validate(settings, folder, maximum=7):
    report = initial_report(settings, maximum)
    if not settings.api_key:
        report['reason'] = '未配置 OPENAI_API_KEY；未启动真实测试，未回退 Mock。请仅在 backend/.env 本地配置。'
        return report, 2
    original = llm.complete
    audit = RequestAudit(original, maximum)
    llm.complete = audit.complete
    report['execution_mode'] = 'live'
    try:
        report['active_check'] = 'connectivity'
        async with asyncio.timeout(310):
            reply = await llm.complete(settings, [{'role': 'user', 'content': '请仅回复 OK。'}], [])
            require(reply.get('content') and not reply.get('tool_calls'), '连通性请求未获得纯文本回复')
            report['checks']['connectivity'] = 'PASS'
            await business_checks(settings, folder, audit, report)
        report['conclusion'] = 'A'
        return report, 0
    except Exception as exc:
        report['checks'][report.get('active_check', 'connectivity')] = 'FAIL'
        report['error'] = str(exc)[:1000] if isinstance(exc, (llm.ModelError, ValueError)) else type(exc).__name__
        report['conclusion'] = 'B' if 'PASS' in report['checks'].values() else 'FAILED_BEFORE_BUSINESS'
        return report, 1
    finally:
        llm.complete = original
        report['external_requests_attempted'] = len(audit.entries)
        report['trace'] = audit.entries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--max-requests', type=int, default=7, choices=range(1, 13), metavar='1..12')
    args = parser.parse_args()
    settings = Settings()
    # Silence HTTP libraries so local session tokens / credentials never appear in this runner's log URLs.
    for name in ('httpx', 'httpcore', 'websockets', 'uvicorn.access'):
        logging.getLogger(name).setLevel(logging.CRITICAL)
    folder = ROOT / 'artifacts' / 'real-llm' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid4().hex[:6])
    folder.mkdir(parents=True)
    if settings.api_key:
        report, exit_code = asyncio.run(validate(settings, folder, args.max_requests))
    else:
        # Even an event loop may need local sockets on Windows; no credentials means no network setup at all.
        report, exit_code = initial_report(settings, args.max_requests), 2
        report['reason'] = '未配置 OPENAI_API_KEY；未启动真实测试，未回退 Mock。请仅在 backend/.env 本地配置。'
    report = clean(report, settings.api_key)
    target = folder / 'report.json'
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'conclusion': report['conclusion'], 'checks': report['checks'],
                      'external_requests_attempted': report['external_requests_attempted'], 'report': str(target)}, ensure_ascii=False, indent=2))
    return exit_code


if __name__ == '__main__':
    raise SystemExit(main())
