from fastapi.testclient import TestClient

from app.main import create_app
from app.config import Settings
from conftest import receive_until, send


def test_two_clients_broadcast_and_room_isolation(client, identity):
    a, headers = identity
    b = client.post('/api/users', json={'nickname': '另一位用户'}).json()
    room = client.get('/api/rooms').json()[0]
    other = client.post('/api/rooms', headers=headers, json={'name': '独立房间'}).json()
    with client.websocket_connect(f'/ws/rooms/{room["id"]}?token={a["token"]}') as wa:
        receive_until(wa, lambda e: e['type'] == 'snapshot')
        with client.websocket_connect(f'/ws/rooms/{room["id"]}?token={b["token"]}') as wb:
            receive_until(wb, lambda e: e['type'] == 'snapshot')
            send(wa, '你好，实时聊天室', 'sync-1')
            ma = receive_until(wa, lambda e: e['type'] == 'message')['message']
            mb = receive_until(wb, lambda e: e['type'] == 'message')['message']
            assert ma['id'] == mb['id']
            assert ma['sender_name'] == '测试用户'
            send(wb, '实时收到啦', 'sync-2')
            assert receive_until(wa, lambda e: e['type'] == 'message')['message']['sender_name'] == '另一位用户'
    assert len(client.get(f'/api/rooms/{other["id"]}/state').json()['messages']) == 0
    assert len(client.get(f'/api/rooms/{room["id"]}/state').json()['messages']) == 3


def test_create_bot_mention_calculator_and_tool_persistence(client, identity):
    user, headers = identity
    room = client.get('/api/rooms').json()[0]['id']
    bot = client.post('/api/bots', headers=headers, json={'name': '自建助手', 'role': '算术助手',
        'system_prompt': '请使用计算器。', 'tools': ['calculator']}).json()
    assert client.put(f'/api/rooms/{room}/bots', headers=headers, json={'bot_ids': [bot['id']]}).status_code == 200
    with client.websocket_connect(f'/ws/rooms/{room}?token={user["token"]}') as ws:
        receive_until(ws, lambda e: e['type'] == 'snapshot')
        send(ws, '@自建助手 计算 (128 + 256) * 3', 'calc-1')
        reply = receive_until(ws, lambda e: e['type'] == 'message' and e['message']['kind'] == 'bot')['message']
        assert '1152' in reply['content'] and 'Demo / Mock' in reply['content']
    state = client.get(f'/api/rooms/{room}/state').json()
    assert state['tasks'][0]['status'] == 'completed'
    assert state['tool_calls'][0]['name'] == 'calculator'
    assert state['tool_calls'][0]['status'] == 'completed'
    assert state['tool_calls'][0]['input']['expression'] == '(128 + 256) * 3'
    assert '1152' in state['tool_calls'][0]['output']


def test_delegation_child_returns_to_parent(client, identity):
    user, _ = identity
    room = client.get('/api/rooms').json()[0]['id']
    with client.websocket_connect(f'/ws/rooms/{room}?token={user["token"]}') as ws:
        receive_until(ws, lambda e: e['type'] == 'snapshot')
        send(ws, '@策划官 请委派给计算员计算 99 * 12，并汇总', 'delegate-1')
        reply = receive_until(ws, lambda e: e['type'] == 'message' and e['message']['kind'] == 'bot')['message']
        assert reply['sender_name'] == '策划官'
        assert '1188' in reply['content'] and '策划官 → 计算员 → 策划官' in reply['content']
    state = client.get(f'/api/rooms/{room}/state').json()
    root = next(t for t in state['tasks'] if t['depth'] == 0)
    child = next(t for t in state['tasks'] if t['depth'] == 1)
    assert child['parent_id'] == root['id'] and child['root_id'] == root['id']
    assert all(t['status'] == 'completed' for t in state['tasks'])
    assert {t['name'] for t in state['tool_calls']} == {'calculator', 'delegate_to_bot'}
    assert next(c for c in state['tool_calls'] if c['name'] == 'delegate_to_bot')['child_task_id'] == child['id']
    detail = client.get(f'/api/tasks/{child["id"]}').json()
    assert detail['root_id'] == root['id'] and len(detail['tasks']) == 2 and len(detail['tool_calls']) == 2


def test_persistence_across_app_restart(tmp_path):
    settings = Settings(database_url='sqlite:///' + (tmp_path / 'persist.db').as_posix(), mode='demo')
    with TestClient(create_app(settings)) as c:
        user = c.post('/api/users', json={'nickname': '持久化用户'}).json()
        room = c.get('/api/rooms').json()[0]['id']
        with c.websocket_connect(f'/ws/rooms/{room}?token={user["token"]}') as ws:
            receive_until(ws, lambda e: e['type'] == 'snapshot')
            send(ws, '@计算员 计算 6 * 7', 'persist-1')
            receive_until(ws, lambda e: e['type'] == 'message' and e['message']['kind'] == 'bot')
        original = c.get(f'/api/rooms/{room}/state').json()
    with TestClient(create_app(settings)) as c:
        restored = c.get(f'/api/rooms/{room}/state').json()
        for key in ['bots', 'messages', 'tasks', 'tool_calls']:
            assert restored[key] == original[key]
        assert c.get('/api/me', headers={'Authorization': 'Bearer ' + user['token']}).status_code == 200


def test_validation_deduplication_and_no_prefix_mentions(client, identity):
    user, headers = identity
    assert client.post('/api/users', json={'nickname': '   '}).status_code == 422
    assert client.post('/api/bots', headers=headers, json={'name': 'bad name', 'role': 'x', 'system_prompt': 'x'}).status_code == 422
    assert client.post('/api/rooms', json={'name': 'x'}).status_code == 401
    room = client.get('/api/rooms').json()[0]['id']
    with client.websocket_connect(f'/ws/rooms/{room}?token={user["token"]}') as ws:
        receive_until(ws, lambda e: e['type'] == 'snapshot')
        ws.send_text('{bad json')
        receive_until(ws, lambda e: e['type'] == 'error')
        ws.send_json({'type': 'message', 'content': ' ', 'client_id': 'bad'})
        receive_until(ws, lambda e: e['type'] == 'error')
        send(ws, '@计算员extra 不应触发', 'unique-1')
        a = receive_until(ws, lambda e: e['type'] == 'message')['message']
        send(ws, '@计算员extra 不应触发', 'unique-1')
        b = receive_until(ws, lambda e: e['type'] == 'message')['message']
        assert a['id'] == b['id']
    state = client.get(f'/api/rooms/{room}/state').json()
    assert not state['tasks'] and len(state['messages']) == 2


def test_history_pagination(client, identity):
    user, _ = identity
    room = client.get('/api/rooms').json()[0]['id']
    with client.websocket_connect(f'/ws/rooms/{room}?token={user["token"]}') as ws:
        receive_until(ws, lambda e: e['type'] == 'snapshot')
        for i in range(4):
            send(ws, f'msg-{i}', f'page-{i}')
            receive_until(ws, lambda e: e['type'] == 'message')
    page = client.get(f'/api/rooms/{room}/messages?limit=2').json()
    assert page['has_more'] and [m['content'] for m in page['messages']] == ['msg-2', 'msg-3']
    older = client.get(f'/api/rooms/{room}/messages?limit=2&before_id={page["messages"][0]["id"]}').json()
    assert [m['content'] for m in older['messages']] == ['msg-0', 'msg-1']
