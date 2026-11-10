import asyncio
import json

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app import llm
from app.agent import Budget
from app.config import Settings
from app.main import create_app
from app.models import Message, Task, ToolCall, uid
from conftest import receive_until, send


def test_shared_budget_self_and_depth_guards(client, app):
    runner = app.state.runner
    room = client.get('/api/rooms').json()[0]['id']
    bot = next(b for b in runner.peers(room) if b['name'] == '策划官')
    with Session(app.state.engine) as s:
        trigger = s.exec(select(Message)).first()

    async def scenario():
        root = await runner.create_task(room, bot, 'guard test', trigger.id)
        budget = Budget()
        result = await runner.execute_tool(root, bot, 'delegate_to_bot', {'bot_name': bot['name'], 'task': 'self'}, budget)
        assert '自身' in result
        root.depth = 2
        result = await runner.execute_tool(root, bot, 'delegate_to_bot', {'bot_name': '计算员', 'task': 'too deep'}, budget)
        assert '深度 2' in result
        for _ in range(4):
            await runner.execute_tool(root, bot, 'calculator', {'expression': '1+1'}, budget)
        with pytest.raises(ValueError, match='6'):
            await runner.execute_tool(root, bot, 'calculator', {'expression': '1+1'}, budget)
        assert budget.used == 6
    asyncio.run(scenario())
    with Session(app.state.engine) as s:
        calls = s.exec(select(ToolCall)).all()
        assert len(calls) == 6 and calls[0].status == 'failed' and calls[1].status == 'failed'


def test_live_function_protocol_and_delegation(tmp_path, monkeypatch):
    settings = Settings(database_url='sqlite:///' + (tmp_path / 'live.db').as_posix(), mode='live', api_key='test-not-a-real-key')
    seen = []

    async def fake_complete(_settings, messages, schemas):
        seen.append((messages.copy(), schemas))
        tools = [m for m in messages if m['role'] == 'tool']
        is_analyst = '你是计算员' in messages[0]['content']
        if tools:
            assert tools[-1]['tool_call_id'] in {'calc-call', 'delegate-call'}
            return {'role': 'assistant', 'content': '真实协议测试汇总：' + tools[-1]['content']}
        name, args, cid = ('calculator', {'expression': '21*2'}, 'calc-call') if is_analyst else (
            'delegate_to_bot', {'bot_name': '计算员', 'task': '计算 21*2'}, 'delegate-call')
        assert name in [t['function']['name'] for t in schemas]
        return {'role': 'assistant', 'content': None, 'tool_calls': [
            {'id': cid, 'type': 'function', 'function': {'name': name, 'arguments': json.dumps(args, ensure_ascii=False)}}]}
    monkeypatch.setattr(llm, 'complete', fake_complete)
    with TestClient(create_app(settings)) as c:
        user = c.post('/api/users', json={'nickname': 'live-test'}).json()
        room = c.get('/api/rooms').json()[0]['id']
        with c.websocket_connect(f'/ws/rooms/{room}?token={user["token"]}') as ws:
            receive_until(ws, lambda e: e['type'] == 'snapshot')
            send(ws, '@策划官 委派计算 21*2', 'live-test')
            message = receive_until(ws, lambda e: e['type'] == 'message' and e['message']['kind'] == 'bot')['message']
            assert '42' in message['content'] and message['mode'] == 'live'
        assert len(seen) == 4
        state = c.get(f'/api/rooms/{room}/state').json()
        assert len(state['tasks']) == 2 and len(state['tool_calls']) == 2


def test_model_failure_is_visible_and_persisted(tmp_path, monkeypatch):
    async def fail(*_):
        raise llm.ModelError('模型 API 返回 HTTP 401，请检查 Key。')
    monkeypatch.setattr(llm, 'complete', fail)
    app = create_app(Settings(database_url='sqlite:///' + (tmp_path / 'failed.db').as_posix(), mode='live', api_key='fake'))
    with TestClient(app) as c:
        user = c.post('/api/users', json={'nickname': 'failure-test'}).json()
        room = c.get('/api/rooms').json()[0]['id']
        with c.websocket_connect(f'/ws/rooms/{room}?token={user["token"]}') as ws:
            receive_until(ws, lambda e: e['type'] == 'snapshot')
            send(ws, '@计算员 你好', 'failure')
            error = receive_until(ws, lambda e: e['type'] == 'message' and e['message']['kind'] == 'system')['message']
            assert '401' in error['content']
        task = c.get(f'/api/rooms/{room}/tasks').json()['tasks'][0]
        assert task['status'] == 'failed' and '401' in task['error']


def test_live_without_key_reports_error():
    with pytest.raises(llm.ModelError, match='OPENAI_API_KEY'):
        asyncio.run(llm.complete(Settings(mode='live', api_key=''), [], []))


@pytest.mark.parametrize('scenario', ['nested_depth', 'shared_budget'])
def test_limits_hold_across_real_agent_loop_and_children(tmp_path, monkeypatch, scenario):
    settings = Settings(database_url='sqlite:///' + (tmp_path / 'limits.db').as_posix(), mode='live', api_key='test-only')

    async def fake_complete(_settings, messages, _schemas):
        results = [m for m in messages if m['role'] == 'tool']
        root = '你是策划官' in messages[0]['content']
        analyst = '你是计算员' in messages[0]['content']
        if results and (scenario == 'nested_depth' or root):
            return {'role': 'assistant', 'content': '执行汇总：' + results[-1]['content']}
        if root:
            name, args = 'delegate_to_bot', {'bot_name': '计算员', 'task': '执行子任务'}
        elif scenario == 'shared_budget':
            name, args = 'calculator', {'expression': '6*7'}
        else:
            name, args = 'delegate_to_bot', {'bot_name': '深层助手' if analyst else '策划官', 'task': '继续委派'}
        return {'role': 'assistant', 'content': None, 'tool_calls': [{'id': f'call-{len(results)}', 'type': 'function',
            'function': {'name': name, 'arguments': json.dumps(args, ensure_ascii=False)}}]}

    monkeypatch.setattr(llm, 'complete', fake_complete)
    app = create_app(settings)
    with TestClient(app) as c:
        user = c.post('/api/users', json={'nickname': 'limit-test'}).json()
        headers = {'Authorization': 'Bearer ' + user['token']}
        room = c.get('/api/rooms').json()[0]['id']
        if scenario == 'nested_depth':
            with Session(app.state.engine) as s:
                from app.models import Bot
                analyst = s.exec(select(Bot).where(Bot.name == '计算员')).first()
                analyst.tools = ['calculator', 'delegate_to_bot']
                s.add(analyst); s.commit()
            third = c.post('/api/bots', headers=headers, json={'name': '深层助手', 'role': 'depth test',
                'system_prompt': 'DEPTH_C', 'tools': ['delegate_to_bot']}).json()
            ids = [b['id'] for b in c.get('/api/bots').json()]
            assert third['id'] in ids
            c.put(f'/api/rooms/{room}/bots', headers=headers, json={'bot_ids': ids})
        with c.websocket_connect(f'/ws/rooms/{room}?token={user["token"]}') as ws:
            receive_until(ws, lambda e: e['type'] == 'snapshot')
            send(ws, '@策划官 验证协作上限', scenario)
            receive_until(ws, lambda e: e['type'] == 'message' and e['message']['task_id'] is not None)
        state = c.get(f'/api/rooms/{room}/tasks').json()
        assert next(t for t in state['tasks'] if t['parent_id'] is None)['status'] == 'failed'
        assert max(t['depth'] for t in state['tasks']) <= 2
        if scenario == 'nested_depth':
            assert len(state['tasks']) == 3 and len(state['tool_calls']) == 3
            assert any(t['status'] == 'failed' and '深度' in t['output'] for t in state['tool_calls'])
        else:
            assert len(state['tasks']) == 2 and len(state['tool_calls']) == 6
            assert any(t['status'] == 'failed' and '6' in t['error'] for t in state['tasks'])


def test_auto_without_key_is_demo():
    assert Settings(mode='auto', api_key='').demo
    assert not Settings(mode='auto', api_key='configured').demo


def test_http_compatible_transport(monkeypatch):
    requests = []
    transport = httpx.MockTransport(lambda req: (
        requests.append(req) or httpx.Response(200, json={'choices': [{'message': {'role': 'assistant', 'content': 'ok'}}]})))
    real_client = httpx.AsyncClient
    monkeypatch.setattr(llm.httpx, 'AsyncClient', lambda **kw: real_client(transport=transport, **kw))
    result = asyncio.run(llm.complete(Settings(api_key='private-test', base_url='https://example.test/v1/', model='custom'),
                                       [{'role': 'user', 'content': 'hello'}], []))
    assert result['content'] == 'ok'
    assert str(requests[0].url) == 'https://example.test/v1/chat/completions'
    assert requests[0].headers['authorization'] == 'Bearer private-test'
    assert json.loads(requests[0].content)['model'] == 'custom'


def test_restart_marks_interrupted_records_failed(tmp_path):
    settings = Settings(database_url='sqlite:///' + (tmp_path / 'interrupted.db').as_posix(), mode='demo')
    app = create_app(settings)
    with TestClient(app) as c:
        room = c.get('/api/rooms').json()[0]['id']
        bot = app.state.runner.peers(room)[0]
        with Session(app.state.engine) as s:
            trigger = s.exec(select(Message)).first()
            root_id = uid()
            task = Task(id=root_id, room_id=room, bot_id=bot['id'], bot_name=bot['name'], root_id=root_id,
                        trigger_message_id=trigger.id, input='unfinished', mode='demo')
            s.add(task); s.commit(); s.refresh(task)
            s.add(ToolCall(room_id=room, task_id=task.id, root_id=task.root_id, name='calculator'))
            s.commit()
    with TestClient(create_app(settings)) as c:
        state = c.get(f'/api/rooms/{room}/tasks').json()
        assert state['tasks'][0]['status'] == state['tool_calls'][0]['status'] == 'failed'
