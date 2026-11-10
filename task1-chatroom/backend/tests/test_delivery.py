"""Final acceptance tests. HTTP transport fixtures are not real model results."""
import asyncio
import json

import httpx
import pytest
from fastapi.testclient import TestClient

from app import llm
from app.config import Settings
from app.main import create_app
from conftest import receive_until, send


@pytest.mark.parametrize('recover', [False, True])
def test_native_http_tool_chain_and_parent_continuation(tmp_path, monkeypatch, recover):
    requests = []
    key = 'fixture-credential-not-a-real-key'

    def provider(req):
        body = json.loads(req.content)
        requests.append(body)
        assert str(req.url) == 'https://fixture.invalid/v1/chat/completions'
        assert req.headers['Authorization'] == 'Bearer ' + key
        assert body['model'] == 'fixture-tool-model'
        assert key not in json.dumps(body)
        messages = body['messages']
        planner = '你是规划助手' in messages[0]['content']
        outputs = [m for m in messages if m['role'] == 'tool']
        assert {t['function']['name'] for t in body['tools']} >= {'calculator'}
        if outputs and not (recover and not planner and len(outputs) == 1):
            # This final request must include the original assistant tool call and its correlated result.
            for output in outputs:
                assert any(output['tool_call_id'] == c['id'] for m in messages for c in m.get('tool_calls', []) or [])
            assert '42' in outputs[-1]['content']
            text = '规划助手最终总结：子 Bot 已完成计算，答案为 42。' if planner else '数据助手计算结果：42。'
            message = {'role': 'assistant', 'content': text}
        else:
            name = 'delegate_to_bot' if planner else 'calculator'
            args = {'bot_name': '数据助手', 'task': '调用计算器计算 6*7，然后返回结果'} if planner else {
                'expression': '1/0' if recover and not outputs else '6*7'}
            message = {'role': 'assistant', 'content': None, 'tool_calls': [{'id': f'{name}-{len(outputs)}', 'type': 'function',
                       'function': {'name': name, 'arguments': json.dumps(args, ensure_ascii=False)}}]}
        return httpx.Response(200, json={'choices': [{'message': message, 'finish_reason': 'tool_calls' if message.get('tool_calls') else 'stop'}]})

    real_client = httpx.AsyncClient
    monkeypatch.setattr(llm.httpx, 'AsyncClient', lambda **kw: real_client(transport=httpx.MockTransport(provider), **kw))
    settings = Settings(database_url='sqlite:///' + (tmp_path / 'wire.db').as_posix(), mode='live',
                        api_key=key, base_url='https://fixture.invalid/v1', model='fixture-tool-model')
    with TestClient(create_app(settings)) as c:
        user = c.post('/api/users', json={'nickname': '协议验收'}).json()
        headers = {'Authorization': 'Bearer ' + user['token']}
        room = c.get('/api/rooms').json()[0]['id']
        bots = [c.post('/api/bots', headers=headers, json={
            'name': name, 'role': name, 'system_prompt': '你是' + name,
            'tools': ['calculator', 'delegate_to_bot'] if name == '规划助手' else ['calculator']}).json()
            for name in ('规划助手', '数据助手')]
        c.put(f'/api/rooms/{room}/bots', headers=headers, json={'bot_ids': [b['id'] for b in bots]})
        with c.websocket_connect(f'/ws/rooms/{room}?token={user["token"]}') as ws:
            receive_until(ws, lambda e: e['type'] == 'snapshot')
            send(ws, '@规划助手 委派计算 6*7 后总结', 'wire-test')
            reply = receive_until(ws, lambda e: e['type'] == 'message' and e['message']['kind'] == 'bot')['message']
            assert reply['sender_name'] == '规划助手' and '最终总结' in reply['content'] and '42' in reply['content']
            assert reply['mode'] == 'live'  # This is the live code path against a fixture, not an external model.
        state = c.get(f'/api/rooms/{room}/state').json()
        assert len(requests) == (5 if recover else 4)
        assert len(state['tasks']) == 2 and all(t['status'] == 'completed' for t in state['tasks'])
        assert len(state['tool_calls']) == (3 if recover else 2)
        if recover:
            assert any(t['status'] == 'failed' for t in state['tool_calls'])
        assert key not in json.dumps(state)


def test_demo_failed_tool_marks_task_failed(client, identity):
    user, _ = identity
    room = client.get('/api/rooms').json()[0]['id']
    with client.websocket_connect(f'/ws/rooms/{room}?token={user["token"]}') as ws:
        receive_until(ws, lambda e: e['type'] == 'snapshot')
        send(ws, '@计算员 计算 1 / 0', 'failed-calculator')
        error = receive_until(ws, lambda e: e['type'] == 'message' and e['message']['task_id'] is not None)['message']
        assert error['kind'] == 'system' and '任务失败' in error['content'] and '除零' in error['content']
    state = client.get(f'/api/rooms/{room}/state').json()
    assert state['tasks'][0]['status'] == 'failed'
    assert state['tool_calls'][0]['status'] == 'failed'


@pytest.mark.parametrize('case', ['http401', 'http429', 'timeout', 'bad_json', 'missing_id', 'bad_calls', 'truncated'])
def test_provider_errors_fail_task_without_leaking_secrets(tmp_path, monkeypatch, caplog, case):
    secret = 'fixture-secret-value-do-not-persist'

    def provider(req):
        if case.startswith('http'):
            return httpx.Response(int(case[4:]), json={'error': {'message': secret}})
        if case == 'timeout':
            raise httpx.ReadTimeout(secret, request=req)
        if case == 'bad_json':
            return httpx.Response(200, text=secret)
        message = {'content': None, 'tool_calls': [{'type': 'function', 'function': {'name': 'calculator', 'arguments': '{}'}}]}
        if case == 'bad_calls':
            message['tool_calls'] = 'not-a-list'
        if case == 'truncated':
            message = {'content': 'unfinished'}
        return httpx.Response(200, json={'choices': [{'message': message, 'finish_reason': 'length' if case == 'truncated' else 'tool_calls'}]})

    real_client = httpx.AsyncClient
    monkeypatch.setattr(llm.httpx, 'AsyncClient', lambda **kw: real_client(transport=httpx.MockTransport(provider), **kw))
    settings = Settings(database_url='sqlite:///' + (tmp_path / 'error.db').as_posix(), mode='live', api_key=secret)
    assert secret not in repr(settings)
    with TestClient(create_app(settings)) as c:
        user = c.post('/api/users', json={'nickname': '失败验收'}).json()
        room = c.get('/api/rooms').json()[0]['id']
        with c.websocket_connect(f'/ws/rooms/{room}?token={user["token"]}') as ws:
            receive_until(ws, lambda e: e['type'] == 'snapshot')
            send(ws, '@计算员 计算 1+1', 'provider-error')
            error = receive_until(ws, lambda e: e['type'] == 'message' and e['message']['task_id'] is not None)['message']
            assert error['kind'] == 'system' and '任务失败' in error['content']
        state = c.get(f'/api/rooms/{room}/state').json()
        assert state['tasks'][0]['status'] == 'failed'
        assert secret not in json.dumps(state) and secret not in caplog.text


def test_task_timeout_cleans_child_tasks_and_tools(tmp_path, monkeypatch):
    async def provider(_settings, messages, _schemas):
        if '你是策划官' in messages[0]['content']:
            return {'role': 'assistant', 'tool_calls': [{'id': 'delegate', 'type': 'function', 'function': {
                'name': 'delegate_to_bot', 'arguments': json.dumps({'bot_name': '计算员', 'task': '计算6*7'})}}]}
        await asyncio.sleep(10)

    monkeypatch.setattr(llm, 'complete', provider)
    app = create_app(Settings(database_url='sqlite:///' + (tmp_path / 'timeout.db').as_posix(), mode='live', api_key='fixture-only'))
    app.state.runner.task_timeout = .1
    with TestClient(app) as c:
        user = c.post('/api/users', json={'nickname': '超时验收'}).json()
        room = c.get('/api/rooms').json()[0]['id']
        with c.websocket_connect(f'/ws/rooms/{room}?token={user["token"]}') as ws:
            receive_until(ws, lambda e: e['type'] == 'snapshot')
            send(ws, '@策划官 委派计算6*7', 'timeout-chain')
            error = receive_until(ws, lambda e: e['type'] == 'message' and e['message']['task_id'] is not None)['message']
            assert error['kind'] == 'system'
        state = c.get(f'/api/rooms/{room}/state').json()
        assert len(state['tasks']) == 2 and all(t['status'] == 'failed' for t in state['tasks'])
        assert state['tool_calls'][0]['status'] == 'failed'


def test_settings_environment_and_secret_redaction(monkeypatch, client, app, caplog):
    monkeypatch.setenv('OPENAI_API_KEY', 'fixture-private-credential')
    monkeypatch.setenv('OPENAI_BASE_URL', 'https://fixture.invalid/v1/')
    monkeypatch.setenv('OPENAI_MODEL', 'configured-model')
    monkeypatch.setenv('LLM_MODE', 'live')
    settings = Settings()
    assert settings.api_key == 'fixture-private-credential' and settings.base_url == 'https://fixture.invalid/v1'
    assert settings.model == 'configured-model' and not settings.demo
    app.state.runner.settings = settings
    assert settings.api_key not in app.state.runner.public_error(ValueError(settings.api_key))
    app.state.runner.public_error(RuntimeError(settings.api_key))
    assert settings.api_key not in caplog.text
    assert Settings(mode='auto', api_key='   ').demo
    with pytest.raises(ValueError, match='OPENAI_BASE_URL'):
        Settings(base_url='https://fixture.invalid/v1?api_key=secret')
